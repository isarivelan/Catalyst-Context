"""Deploy Catalyst Context space, RAW tables, data model, and transformation jobs.

You run this on a machine that can reach your CDF project.

  cd c:\\code\\catalyst-context
  copy .env.example .env
  .\\.venv\\Scripts\\python.exe scripts\\deploy_cdf.py
  .\\.venv\\Scripts\\python.exe scripts\\deploy_cdf.py --run-jobs --seed-instances
  .\\.venv\\Scripts\\python.exe scripts\\deploy_cdf.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SPACE = "catalyst_context"
MODEL_ID = "CatalystContext"
MODEL_VERSION = "v1"
RAW_DB = "catalyst_context_raw"
RAW_TABLES = ("equipment", "timeseries", "events")

JOBS = (
    {
        "external_id": "tr-catalyst-raw-to-equipment",
        "name": "RAW equipment → Equipment instances",
        "sql": ROOT / "cdf" / "transformations" / "tr_raw_to_equipment.sql",
        "destination_type": "Equipment",
    },
    {
        "external_id": "tr-catalyst-raw-to-signals",
        "name": "RAW tags → ProcessSignal instances",
        "sql": ROOT / "cdf" / "transformations" / "tr_raw_to_signals.sql",
        "destination_type": "ProcessSignal",
    },
    {
        "external_id": "tr-catalyst-raw-to-events",
        "name": "RAW events → ProcessEvent instances",
        "sql": ROOT / "cdf" / "transformations" / "tr_raw_to_events.sql",
        "destination_type": "ProcessEvent",
    },
)


def log(msg: str) -> None:
    print(msg, flush=True)


def fail(msg: str, code: int = 1) -> int:
    print(f"ERROR: {msg}", file=sys.stderr)
    return code


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deploy Catalyst Context to Cognite Data Fusion")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan only; do not call CDF")
    parser.add_argument("--run-jobs", action="store_true", help="Start the three transformation jobs after creating them")
    parser.add_argument(
        "--seed-instances",
        action="store_true",
        help="Also upsert Equipment / ProcessSignal / ProcessEvent nodes via the SDK",
    )
    parser.add_argument("--skip-model", action="store_true", help="Skip GraphQL data-model publish")
    return parser.parse_args(argv)


def read_csv(name: str) -> list[dict[str, str]]:
    path = ROOT / "cdf" / "raw" / f"{name}.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def graphql_dml() -> str:
    return (ROOT / "cdf" / "data_models" / "CatalystContext.graphql").read_text(encoding="utf-8").strip()


def connect():
    from catalyst_context.cdf_client import connect as cdf_connect
    from catalyst_context.config import load_cdf_settings

    settings = load_cdf_settings()
    if not settings.ready:
        raise SystemExit(
            fail(
                "Missing CDF credentials. Copy .env.example to .env and set "
                "CDF_PROJECT, CDF_CLUSTER, CDF_TENANT_ID, CDF_CLIENT_ID, CDF_CLIENT_SECRET."
            )
        )
    log(f"Connecting to project={settings.project} cluster={settings.cluster}")
    return cdf_connect(settings), settings


def step_space(client) -> None:
    from cognite.client.data_classes.data_modeling import SpaceApply

    log(f"1/5  Apply space `{SPACE}`")
    client.data_modeling.spaces.apply(
        SpaceApply(space=SPACE, name="Catalyst Context", description="Process-industry POC for pharma and oil & gas")
    )


def step_raw(client) -> None:
    from cognite.client.data_classes.raw import RowWrite

    log(f"2/5  Load RAW `{RAW_DB}`")
    for table in RAW_TABLES:
        rows = read_csv(table)
        payload = [RowWrite(key=row["external_id"], columns=row) for row in rows]
        client.raw.rows.insert(RAW_DB, table, payload, ensure_parent=True)
        log(f"     {table}: {len(payload)} rows")


def step_model(client):
    log(f"3/5  Publish data model `{SPACE}:{MODEL_ID}/{MODEL_VERSION}`")
    result = client.data_modeling.graphql.apply_dml(
        id=(SPACE, MODEL_ID, MODEL_VERSION),
        dml=graphql_dml(),
        name="Catalyst Context",
        description="Shared process-industry model for life sciences and oil and gas",
    )
    log(f"     published {result.space}:{result.external_id}/{result.version}")
    return result


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

    log("4/5  Upsert transformation jobs")
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
            query=job["sql"].read_text(encoding="utf-8"),
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
    log("5/5  Run transformation jobs")
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
    log("     Seeding data-model instances from RAW CSVs")
    nodes = []
    for row in read_csv("equipment"):
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
    log(f"  graphql:          cdf/data_models/CatalystContext.graphql")
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
            published = step_model(client)
            version = published.version or MODEL_VERSION
        else:
            log("3/5  Skip data model")
        step_jobs(client, settings)
        if args.seed_instances:
            step_seed(client, version)
        if args.run_jobs:
            step_run(client)
        else:
            log("5/5  Jobs created but not started. Re-run with --run-jobs to execute them.")
        log("Done.")
        log("In Fusion: Data models -> catalyst_context / CatalystContext v1")
        log("           Transform -> tr-catalyst-raw-to-*")
        return 0
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 1
    except Exception as exc:
        return fail(f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
