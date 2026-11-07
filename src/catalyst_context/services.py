"""Catalog access for demo and live CDF modes."""

from __future__ import annotations

import json

import pandas as pd

from catalyst_context.cdf_client import connect, load_live_catalog, retrieve_datapoints
from catalyst_context.config import CdfSettings, load_cdf_settings
from catalyst_context.mock_data import Catalog, datapoints, demo_catalog


def settings() -> CdfSettings:
    return load_cdf_settings()


def load_catalog(mode: str, industry: str, live_client=None) -> Catalog:
    if mode == "live":
        if live_client is None:
            live_client = connect(load_cdf_settings())
        catalog = load_live_catalog(live_client)
    else:
        catalog = demo_catalog()
    return catalog.filter_industry(industry)


def signal_frame(mode: str, ts: dict, live_client=None) -> pd.DataFrame:
    if mode == "live" and live_client is not None and ts.get("id"):
        try:
            frame = retrieve_datapoints(live_client, int(ts["id"]), ts["external_id"])
            if not frame.empty:
                return frame
        except Exception:
            pass
    return datapoints(ts["external_id"])


def children(catalog: Catalog, parent_external_id: str | None) -> list[dict]:
    return [a for a in catalog.assets if a.get("parent_external_id") == parent_external_id]


def roots(catalog: Catalog) -> list[dict]:
    ids = {a["external_id"] for a in catalog.assets}
    return [
        a
        for a in catalog.assets
        if not a.get("parent_external_id") or a.get("parent_external_id") not in ids
    ]


def subtree_ids(catalog: Catalog, asset_ext: str) -> set[str]:
    ids = {asset_ext}
    changed = True
    while changed:
        changed = False
        for asset in catalog.assets:
            parent = asset.get("parent_external_id")
            if parent in ids and asset["external_id"] not in ids:
                ids.add(asset["external_id"])
                changed = True
    return ids


def related_rows(catalog: Catalog, asset_ext: str) -> dict[str, list[dict]]:
    scope = subtree_ids(catalog, asset_ext)
    ts = [t for t in catalog.timeseries if t.get("asset_external_id") in scope]
    events = [e for e in catalog.events if e.get("asset_external_id") in scope]
    files = [f for f in catalog.files if f.get("asset_external_id") in scope]
    rels = [
        r
        for r in catalog.relationships
        if r["source_external_id"] in scope or r["target_external_id"] in scope
    ]
    return {"timeseries": ts, "events": events, "files": files, "relationships": rels}


def context_pack(catalog: Catalog, asset: dict, industry: str) -> dict:
    related = related_rows(catalog, asset["external_id"])
    return {
        "project": catalog.project,
        "mode": catalog.mode,
        "industry_lens": industry,
        "asset": asset,
        "timeseries": related["timeseries"],
        "events": related["events"],
        "files": related["files"],
        "relationships": related["relationships"],
        "batches": catalog.batches if industry in {"pharma", "both"} else [],
    }


def pack_json(pack: dict) -> str:
    return json.dumps(pack, indent=2, default=str)


def timeseries_csv(frame: pd.DataFrame) -> str:
    return frame.to_csv(index_label="timestamp")
