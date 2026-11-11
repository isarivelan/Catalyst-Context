"""Cognite client and CatalystContext view reads."""

from __future__ import annotations

from typing import Any

from catalyst_context import MODEL_ID, MODEL_VERSION, SPACE, VIEWS
from catalyst_context.catalog import Catalog
from catalyst_context.config import CdfSettings, load_cdf_settings


def _patch_pyodide_http() -> None:
    try:
        import pyodide_http

        pyodide_http.patch_all()
    except Exception:
        pass


def get_client():
    _patch_pyodide_http()
    try:
        from cognite.client import CogniteClient
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "Package 'cognite-sdk' is not installed in this Streamlit runtime. "
            "Add 'cognite-sdk' to the app requirements.txt and republish."
        ) from exc

    # Fusion Streamlit injects the signed-in user. Try that first.
    try:
        client = CogniteClient()
        if getattr(client.config, "project", None):
            return client
    except Exception:
        pass
    settings = load_cdf_settings()
    if settings.ready:
        return connect(settings)
    raise ValueError(
        "No CDF credentials. In Fusion this app uses the signed-in user. "
        "Locally set IDP_TENANT_ID, IDP_CLIENT_ID, IDP_CLIENT_SECRET, CDF_PROJECT, CDF_CLUSTER."
    )


def connect(settings: CdfSettings):
    from cognite.client import ClientConfig, CogniteClient
    from cognite.client.credentials import OAuthClientCredentials

    token_args = {}
    if settings.audience:
        token_args["audience"] = settings.audience
    creds = OAuthClientCredentials(
        token_url=settings.token_url,
        client_id=settings.client_id,
        client_secret=settings.client_secret,
        scopes=settings.scopes,
        **token_args,
    )
    return CogniteClient(
        ClientConfig(
            client_name="catalyst-context-app",
            project=settings.project,
            credentials=creds,
            base_url=settings.base_url,
        )
    )


def _view_id(name: str):
    from cognite.client.data_classes.data_modeling import ViewId

    return ViewId(SPACE, name, MODEL_VERSION)


def _rel_ext(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return str(value.get("externalId") or value.get("external_id") or "")
    return str(getattr(value, "external_id", "") or "")


def _props(node: Any, view_name: str) -> dict[str, Any]:
    raw = getattr(node, "properties", None) or {}
    items = raw.items() if hasattr(raw, "items") else []
    for key, val in items:
        name = getattr(key, "external_id", None)
        if name is None and isinstance(key, tuple) and len(key) >= 2:
            name = key[1]
        if name == view_name:
            return dict(val or {})
    return {}


def list_view(client, view_name: str, limit: int = 1000) -> list[tuple[str, dict[str, Any]]]:
    from cognite.client.data_classes.data_modeling import NodeId

    vid = _view_id(view_name)
    nodes = client.data_modeling.instances.list(
        instance_type="node",
        sources=vid,
        space=SPACE,
        limit=limit,
    )
    rows = []
    for node in nodes:
        ext = getattr(node, "external_id", None)
        if not ext and isinstance(node, NodeId):
            ext = node.external_id
        rows.append((str(ext), _props(node, view_name)))
    return rows


def load_model_catalog(client) -> Catalog:
    sites = list_view(client, "Site")
    equipment = list_view(client, "Equipment")
    signals = list_view(client, "ProcessSignal")
    events = list_view(client, "ProcessEvent")
    files = list_view(client, "EngineeringFile")
    batches = list_view(client, "Batch")
    quality = list_view(client, "QualityResult")

    assets: list[dict] = []
    relationships: list[dict] = []

    for ext, props in sites:
        assets.append(
            {
                "external_id": ext,
                "name": props.get("name") or ext,
                "description": props.get("description") or "",
                "parent_external_id": None,
                "industry": props.get("industry") or "",
                "kind": "Site",
                "region": props.get("region") or "",
            }
        )

    for ext, props in equipment:
        parent = _rel_ext(props.get("parent"))
        site = _rel_ext(props.get("site"))
        assets.append(
            {
                "external_id": ext,
                "name": props.get("name") or ext,
                "description": props.get("description") or "",
                "parent_external_id": parent or None,
                "site_external_id": site,
                "industry": props.get("industry") or "",
                "kind": props.get("kind") or "Equipment",
                "criticality": props.get("criticality") or "",
            }
        )
        if parent:
            relationships.append({"source_external_id": ext, "target_external_id": parent, "type": "parent"})
        if site:
            relationships.append({"source_external_id": ext, "target_external_id": site, "type": "site"})

    timeseries = []
    for ext, props in signals:
        eq = _rel_ext(props.get("equipment"))
        timeseries.append(
            {
                "external_id": ext,
                "name": props.get("name") or ext,
                "asset_external_id": eq,
                "unit": props.get("unit") or "",
                "industry": props.get("industry") or "",
                "external_tag": props.get("externalTag") or ext,
            }
        )
        if eq:
            relationships.append({"source_external_id": ext, "target_external_id": eq, "type": "equipment"})

    event_rows = []
    for ext, props in events:
        eq = _rel_ext(props.get("equipment"))
        event_rows.append(
            {
                "external_id": ext,
                "type": props.get("eventType") or "Event",
                "subtype": props.get("subtype") or "",
                "description": props.get("description") or ext,
                "asset_external_id": eq,
                "industry": props.get("industry") or "",
            }
        )
        if eq:
            relationships.append({"source_external_id": ext, "target_external_id": eq, "type": "equipment"})

    file_rows = []
    for ext, props in files:
        eq = _rel_ext(props.get("equipment"))
        file_rows.append(
            {
                "external_id": ext,
                "name": props.get("name") or ext,
                "mime_type": props.get("mimeType") or "",
                "kind": props.get("kind") or "",
                "asset_external_id": eq,
                "industry": "",
            }
        )
        if eq:
            relationships.append({"source_external_id": ext, "target_external_id": eq, "type": "equipment"})

    batch_rows = []
    for ext, props in batches:
        unit = _rel_ext(props.get("unit"))
        batch_rows.append(
            {
                "external_id": ext,
                "batch_id": props.get("batchId") or ext,
                "recipe": props.get("recipe") or "",
                "status": props.get("status") or "",
                "yield_pct": props.get("yieldPct"),
                "cycle_h": props.get("cycleHours"),
                "deviations": props.get("deviations"),
                "unit": unit,
            }
        )

    for ext, props in quality:
        batch = _rel_ext(props.get("batch"))
        if batch:
            relationships.append({"source_external_id": ext, "target_external_id": batch, "type": "batch"})

    industry_by_asset = {a["external_id"]: a.get("industry") or "" for a in assets}
    for row in file_rows:
        row["industry"] = industry_by_asset.get(row.get("asset_external_id") or "", "")
    for row in batch_rows:
        row["industry"] = industry_by_asset.get(row.get("unit") or "", "pharma")

    quality_rows = []
    for ext, props in quality:
        batch = _rel_ext(props.get("batch"))
        lab = _rel_ext(props.get("lab"))
        quality_rows.append(
            {
                "external_id": ext,
                "test": props.get("test") or ext,
                "status": props.get("status") or "",
                "result": props.get("result") or "",
                "batch": batch,
                "lab": lab,
                "industry": "pharma",
            }
        )

    project = getattr(getattr(client, "config", None), "project", None) or ""
    return Catalog(
        assets=assets,
        timeseries=timeseries,
        events=event_rows,
        files=file_rows,
        relationships=relationships,
        batches=batch_rows,
        quality=quality_rows,
        counts={
            "Site": len(sites),
            "Equipment": len(equipment),
            "ProcessSignal": len(signals),
            "ProcessEvent": len(events),
            "EngineeringFile": len(files),
            "Batch": len(batches),
            "QualityResult": len(quality),
        },
        project=project,
        space=SPACE,
        model=f"{MODEL_ID}/{MODEL_VERSION}",
    )


def retrieve_datapoints(client, external_id: str):
    import pandas as pd

    dps = client.time_series.data.retrieve(external_id=external_id, start="7d-ago", end="now")
    frame = dps.to_pandas()
    if frame.empty:
        return pd.DataFrame()
    if external_id not in frame.columns and len(frame.columns) == 1:
        frame.columns = [external_id]
    return frame


def synthetic_frame(external_id: str, hours: int = 72, offset: float = 0.0):
    import math
    from datetime import datetime, timedelta, timezone

    import pandas as pd

    now = datetime.now(timezone.utc)
    seed = sum(ord(c) for c in external_id)
    n = hours * 4
    index = [now - timedelta(minutes=15 * (n - i)) for i in range(n)]
    base = 40 + (seed % 18) + offset
    values = [base + 7 * math.sin(i / 10.0) + ((i * seed) % 5) * 0.15 for i in range(n)]
    return pd.DataFrame({external_id: values}, index=pd.DatetimeIndex(index))


def signal_frame(client, ts: dict):
    import pandas as pd

    tag = ts.get("external_tag") or ts.get("external_id")
    if not tag:
        return pd.DataFrame()
    try:
        frame = retrieve_datapoints(client, tag)
        if frame is not None and not frame.empty:
            return frame
    except Exception:
        pass
    return synthetic_frame(tag)
