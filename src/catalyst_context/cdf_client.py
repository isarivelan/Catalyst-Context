"""Cognite Data Fusion client using OIDC client credentials."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from catalyst_context.config import CdfSettings
from catalyst_context.mock_data import Catalog


def _iso(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    try:
        millis = int(value)
        if millis > 10_000_000_000:
            millis //= 1000
        return datetime.fromtimestamp(millis, tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return str(value)


def _rel_ext(node: Any) -> str:
    if node is None:
        return ""
    if hasattr(node, "external_id") and node.external_id:
        return str(node.external_id)
    if isinstance(node, dict):
        return str(node.get("externalId") or node.get("external_id") or node)
    return str(node)


def connect(settings: CdfSettings):
    from cognite.client import ClientConfig, CogniteClient
    from cognite.client.credentials import OAuthClientCredentials

    if not settings.ready:
        raise ValueError("CDF settings are incomplete. Fill CDF_PROJECT, cluster, tenant, client id/secret.")

    creds = OAuthClientCredentials(
        token_url=settings.token_url,
        client_id=settings.client_id,
        client_secret=settings.client_secret,
        scopes=settings.scopes,
    )
    config = ClientConfig(
        client_name="catalyst-context-poc",
        project=settings.project,
        credentials=creds,
        base_url=settings.base_url,
    )
    return CogniteClient(config)


def _asset_row(asset: Any) -> dict:
    parent = None
    if getattr(asset, "parent_external_id", None):
        parent = asset.parent_external_id
    meta = dict(asset.metadata or {})
    industry = meta.get("industry") or meta.get("domain") or "live"
    return {
        "id": asset.id,
        "external_id": asset.external_id or str(asset.id),
        "name": asset.name or asset.external_id or str(asset.id),
        "description": asset.description or "",
        "parent_external_id": parent,
        "industry": industry,
        "kind": (asset.metadata or {}).get("type") or "Asset",
        "metadata": meta,
    }


def _ts_row(ts: Any, asset_ext: str | None) -> dict:
    return {
        "id": ts.id,
        "external_id": ts.external_id or str(ts.id),
        "name": ts.name or ts.external_id or str(ts.id),
        "asset_external_id": asset_ext or "",
        "unit": ts.unit or "",
        "industry": "live",
    }


def load_live_catalog(client, limit: int = 200) -> Catalog:
    assets_raw = client.assets.list(limit=limit)
    assets = [_asset_row(a) for a in assets_raw]
    by_id = {a.id: a.external_id or str(a.id) for a in assets_raw}

    ts_raw = client.time_series.list(limit=limit)
    timeseries = []
    for ts in ts_raw:
        asset_ext = None
        if ts.asset_id and ts.asset_id in by_id:
            asset_ext = by_id[ts.asset_id]
        timeseries.append(_ts_row(ts, asset_ext))

    events = []
    try:
        for ev in client.events.list(limit=min(limit, 100)):
            asset_ext = ""
            if ev.asset_ids:
                asset_ext = by_id.get(ev.asset_ids[0], "")
            start = _iso(ev.start_time)
            end = _iso(ev.end_time)
            events.append(
                {
                    "external_id": ev.external_id or str(ev.id),
                    "type": ev.type or "Event",
                    "subtype": ev.subtype or "",
                    "description": ev.description or ev.external_id or "",
                    "asset_external_id": asset_ext,
                    "start_time": start,
                    "end_time": end,
                    "industry": "live",
                }
            )
    except Exception:
        events = []

    files = []
    try:
        for f in client.files.list(limit=min(limit, 80)):
            asset_ext = ""
            if f.asset_ids:
                asset_ext = by_id.get(f.asset_ids[0], "")
            files.append(
                {
                    "external_id": f.external_id or str(f.id),
                    "name": f.name or f.external_id or str(f.id),
                    "mime_type": f.mime_type or "application/octet-stream",
                    "asset_external_id": asset_ext,
                    "industry": "live",
                }
            )
    except Exception:
        files = []

    relationships = []
    try:
        for rel in client.relationships.list(limit=min(limit, 80)):
            relationships.append(
                {
                    "source_external_id": _rel_ext(getattr(rel, "source", None)),
                    "target_external_id": _rel_ext(getattr(rel, "target", None)),
                    "type": getattr(rel, "relationship_type", None) or "related",
                }
            )
    except Exception:
        relationships = []

    project = getattr(getattr(client, "config", None), "project", None) or "cdf"
    return Catalog(
        assets=assets,
        timeseries=timeseries,
        events=events,
        files=files,
        relationships=relationships,
        batches=[],
        mode="live",
        project=project,
    )


def retrieve_datapoints(client, timeseries_id: int, external_id: str):
    import pandas as pd

    dps = client.time_series.data.retrieve(id=timeseries_id, start="7d-ago", end="now")
    frame = dps.to_pandas()
    if frame.empty:
        return pd.DataFrame()
    if external_id not in frame.columns and len(frame.columns) == 1:
        frame.columns = [external_id]
    return frame
