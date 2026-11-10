"""Deploy Catalyst Context space, containers, views, data model, RAW, and jobs.

Canonical resources live in modules/catalyst_context (Cognite Toolkit layout).

  python scripts/deploy_cdf.py
  python scripts/deploy_cdf.py --seed-instances --run-jobs
  python scripts/deploy_cdf.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

MODULE = ROOT / "modules" / "catalyst_context"
DM_DIR = MODULE / "data_modeling"
RAW_DIR = MODULE / "raw"
TR_DIR = MODULE / "transformations"

VARS = {
    "model_space": "catalyst_context",
    "instance_space": "catalyst_context",
    "model_external_id": "CatalystContext",
    "model_version": "v1",
    "raw_db": "catalyst_context_raw",
}

SPACE = VARS["model_space"]
MODEL_ID = VARS["model_external_id"]
MODEL_VERSION = VARS["model_version"]
RAW_DB = VARS["raw_db"]
RAW_TABLES = ("equipment", "timeseries", "events")
SITE_KINDS = {"Site", "Field"}

JOBS = (
    {
        "external_id": "tr-catalyst-raw-to-sites",
        "name": "RAW equipment → Site instances",
        "sql": TR_DIR / "tr_catalyst_raw_to_sites.sql",
        "destination_type": "Site",
    },
    {
        "external_id": "tr-catalyst-raw-to-equipment",
        "name": "RAW equipment → Equipment instances",
        "sql": TR_DIR / "tr_catalyst_raw_to_equipment.sql",
        "destination_type": "Equipment",
    },
    {
        "external_id": "tr-catalyst-raw-to-signals",
        "name": "RAW tags → ProcessSignal instances",
        "sql": TR_DIR / "tr_catalyst_raw_to_signals.sql",
        "destination_type": "ProcessSignal",
    },
    {
        "external_id": "tr-catalyst-raw-to-events",
        "name": "RAW events → ProcessEvent instances",
        "sql": TR_DIR / "tr_catalyst_raw_to_events.sql",
        "destination_type": "ProcessEvent",
    },
)

_PLACEHOLDER = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")


def log(msg: str) -> None:
    print(msg, flush=True)


def fail(msg: str, code: int = 1) -> int:
    print(f"ERROR: {msg}", file=sys.stderr)
    return code


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deploy Catalyst Context to Cognite Data Fusion")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan only; do not call CDF")
    parser.add_argument("--run-jobs", action="store_true", help="Start transformation jobs after creating them")
    parser.add_argument(
        "--seed-instances",
        action="store_true",
        help="Also upsert Site / Equipment / ProcessSignal / ProcessEvent nodes via the SDK",
    )
    parser.add_argument("--skip-model", action="store_true", help="Skip space/container/view/data-model apply")
    parser.add_argument(
        "--graphql",
        action="store_true",
        help="Also publish cdf/data_models/CatalystContext.graphql (can conflict with explicit containers)",
    )
    return parser.parse_args(argv)


def render(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in VARS:
            raise KeyError(f"Unknown template variable {key}")
        return VARS[key]

    return _PLACEHOLDER.sub(repl, text)


def load_yaml(path: Path):
    import yaml

    return yaml.safe_load(render(path.read_text(encoding="utf-8")))


def read_csv(name: str) -> list[dict[str, str]]:
    path = RAW_DIR / f"{name}.Table.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = []
        for row in csv.DictReader(handle):
            row.pop("key", None)
            rows.append(row)
        return rows


def connect():
    from catalyst_context.cdf_client import connect as cdf_connect
    from catalyst_context.config import load_cdf_settings

    settings = load_cdf_settings()
    if not settings.ready:
        raise SystemExit(
            fail(
                "Missing CDF credentials. Copy .env.example to .env and set "
                "CDF_PROJECT, CDF_CLUSTER, IDP_TENANT_ID, IDP_CLIENT_ID, IDP_CLIENT_SECRET "
                "(CDF_TENANT_ID / CDF_CLIENT_ID / CDF_CLIENT_SECRET still work)."
            )
        )
    log(f"Connecting to project={settings.project} cluster={settings.cluster}")
    return cdf_connect(settings), settings


def step_space(client) -> None:
    from cognite.client.data_classes.data_modeling import SpaceApply

    log(f"1/6  Apply space `{SPACE}`")
    client.data_modeling.spaces.apply(SpaceApply.load(load_yaml(DM_DIR / "catalyst_context.Space.yaml")))


def step_raw(client) -> None:
    from cognite.client.data_classes.raw import RowWrite

    log(f"2/6  Load RAW `{RAW_DB}`")
    for table in RAW_TABLES:
        rows = read_csv(table)
        payload = [RowWrite(key=row["external_id"], columns=row) for row in rows]
        client.raw.rows.insert(RAW_DB, table, payload, ensure_parent=True)
        log(f"     {table}: {len(payload)} rows")


def step_model(client) -> str:
    from cognite.client.data_classes.data_modeling import ContainerApply, DataModelApply, ViewApply

    log(f"3/6  Apply containers, views, data model `{SPACE}:{MODEL_ID}/{MODEL_VERSION}`")
    containers = [
        ContainerApply.load(load_yaml(path))
        for path in sorted((DM_DIR / "containers").glob("*.Container.yaml"))
    ]
    client.data_modeling.containers.apply(containers)
    log(f"     containers: {len(containers)}")

    views = [ViewApply.load(load_yaml(path)) for path in sorted((DM_DIR / "views").glob("*.View.yaml"))]
    client.data_modeling.views.apply(views)
    log(f"     views: {len(views)}")

    data_model = DataModelApply.load(load_yaml(DM_DIR / "CatalystContext.DataModel.yaml"))
    client.data_modeling.data_models.apply(data_model)
    log(f"     data model {data_model.space}:{data_model.external_id}/{data_model.version}")
    return data_model.version or MODEL_VERSION


def step_graphql(client) -> None:
    log("     Publish GraphQL DML (optional)")
    dml = (ROOT / "cdf" / "data_models" / "CatalystContext.graphql").read_text(encoding="utf-8").strip()
    result = client.data_modeling.graphql.apply_dml(
        id=(SPACE, MODEL_ID, MODEL_VERSION),
        dml=dml,
        name="Catalyst Context",
        description="Shared process-industry model for life sciences and oil and gas",
    )
    log(f"     graphql {result.space}:{result.external_id}/{result.version}")


def oidc(settings):
    from cognite.client.data_classes.transformations.common import OidcCredentials

    return OidcCredentials(
        client_id=settings.client_id,
        client_secret=settings.client_secret,
        token_uri=settings.token_url,
        cdf_project_name=settings.project,
        scopes=settings.scopes,
    )


def step_jobs(client, settings) -> None:
    from cognite.client.data_classes.transformations import TransformationWrite
    from cognite.client.data_classes.transformations.common import DataModelInfo, TransformationDestination
    from cognite.client.exceptions import CogniteAPIError, CogniteDuplicatedError

    log("4/6  Upsert transformation jobs")
    creds = oidc(settings)
    for job in JOBS:
        dest = TransformationDestination.instances(
            DataModelInfo(
                space=SPACE,
                external_id=MODEL_ID,
                version=MODEL_VERSION,
                destination_type=job["destination_type"],
            ),
            instance_space=SPACE,
        )
        body = TransformationWrite(
            external_id=job["external_id"],
            name=job["name"],
            ignore_null_fields=True,
            query=render(job["sql"].read_text(encoding="utf-8")),
            destination=dest,
            conflict_mode="upsert",
            is_public=True,
            source_oidc_credentials=creds,
            destination_oidc_credentials=creds,
        )
        try:
            client.transformations.create(body)
            log(f"     created {job['external_id']}")
        except (CogniteDuplicatedError, CogniteAPIError) as exc:
            if not (isinstance(exc, CogniteDuplicatedError) or "already exists" in str(exc).lower()):
                raise
            client.transformations.delete(external_id=job["external_id"])
            client.transformations.create(body)
            log(f"     replaced {job['external_id']}")


def step_run(client) -> None:
    log("5/6  Run transformation jobs")
    for job in JOBS:
        log(f"     running {job['external_id']} ...")
        result = client.transformations.run(transformation_external_id=job["external_id"], wait=True, timeout=180)
        log(f"     {job['external_id']}: {getattr(result, 'status', result)}")


def rel(space: str, ext: str | None):
    from cognite.client.data_classes.data_modeling import DirectRelationReference

    if not ext:
        return None
    return DirectRelationReference(space=space, external_id=ext)


def node(space: str, ext: str, view: str, version: str, props: dict):
    from cognite.client.data_classes.data_modeling import NodeApply, NodeOrEdgeData, ViewId

    cleaned = {key: value for key, value in props.items() if value not in (None, "")}
    return NodeApply(
        space=space,
        external_id=ext,
        sources=[NodeOrEdgeData(source=ViewId(space, view, version), properties=cleaned)],
    )


def step_seed(client, version: str) -> None:
    log("6/6  Seeding data-model instances from RAW CSVs")
    nodes = []
    for row in read_csv("equipment"):
        kind = (row.get("kind") or "").strip()
        if kind in SITE_KINDS:
            nodes.append(
                node(
                    SPACE,
                    row["external_id"],
                    "Site",
                    version,
                    {
                        "name": row["name"],
                        "industry": row.get("industry"),
                        "description": row.get("description"),
                    },
                )
            )
            continue
        nodes.append(
            node(
                SPACE,
                row["external_id"],
                "Equipment",
                version,
                {
                    "name": row["name"],
                    "kind": row.get("kind"),
                    "industry": row.get("industry"),
                    "description": row.get("description"),
                    "criticality": row.get("criticality"),
                    "parent": rel(SPACE, row.get("parent_external_id")),
                    "site": rel(SPACE, row.get("site_external_id")),
                },
            )
        )
    for row in read_csv("timeseries"):
        nodes.append(
            node(
                SPACE,
                row["external_id"],
                "ProcessSignal",
                version,
                {
                    "name": row["name"],
                    "unit": row.get("unit"),
                    "externalTag": row["external_id"],
                    "industry": row.get("industry"),
                    "equipment": rel(SPACE, row.get("asset_external_id")),
                },
            )
        )
    for row in read_csv("events"):
        nodes.append(
            node(
                SPACE,
                row["external_id"],
                "ProcessEvent",
                version,
                {
                    "eventType": row.get("type"),
                    "subtype": row.get("subtype"),
                    "description": row.get("description"),
                    "industry": row.get("industry"),
                    "equipment": rel(SPACE, row.get("asset_external_id")),
                },
            )
        )
    client.data_modeling.instances.apply(nodes)
    log(f"     upserted {len(nodes)} instances")


def plan() -> None:
    log("Deploy plan (no CDF calls)")
    log(f"  space:            {SPACE}")
    log(f"  data model:       {SPACE}:{MODEL_ID}/{MODEL_VERSION}")
    log("  module:           modules/catalyst_context")
    log(f"  containers:       {len(list((DM_DIR / 'containers').glob('*.Container.yaml')))}")
    log(f"  views:            {len(list((DM_DIR / 'views').glob('*.View.yaml')))}")
    log(f"  RAW database:     {RAW_DB}")
    for table in RAW_TABLES:
        log(f"    table {table:<12} {len(read_csv(table))} rows")
    for job in JOBS:
        log(f"  job {job['external_id']}")
        log(f"       {job['sql'].relative_to(ROOT)}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.dry_run:
        plan()
        return 0

    try:
        client, settings = connect()
        step_space(client)
        step_raw(client)
        version = MODEL_VERSION
        if not args.skip_model:
            version = step_model(client)
            if args.graphql:
                step_graphql(client)
        else:
            log("3/6  Skip data model")
        step_jobs(client, settings)
        if args.seed_instances:
            step_seed(client, version)
        else:
            log("6/6  Instances not seeded. Re-run with --seed-instances or --run-jobs.")
        if args.run_jobs:
            step_run(client)
        else:
            log("5/6  Jobs created but not started. Re-run with --run-jobs to execute them.")
        log("Done.")
        log("In Fusion: Data models -> catalyst_context / CatalystContext v1")
        log("           Containers and views are listed on that model")
        log("           Transform -> tr-catalyst-raw-to-*")
        return 0
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 1
    except Exception as exc:
        return fail(f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
