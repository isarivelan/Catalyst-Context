"""In-memory catalog shaped from CatalystContext view instances."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import pandas as pd


@dataclass
class Catalog:
    assets: list[dict] = field(default_factory=list)
    timeseries: list[dict] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    files: list[dict] = field(default_factory=list)
    relationships: list[dict] = field(default_factory=list)
    batches: list[dict] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)
    project: str = ""
    space: str = "catalyst_context"
    model: str = "CatalystContext/v1"

    def filter_industry(self, industry: str) -> "Catalog":
        if industry == "both":
            return self

        def keep(rows: list[dict]) -> list[dict]:
            return [row for row in rows if row.get("industry") in {industry, None, ""}]

        assets = keep(self.assets)
        ids = {a["external_id"] for a in assets}
        ts = [t for t in keep(self.timeseries) if not t.get("asset_external_id") or t["asset_external_id"] in ids]
        events = [e for e in keep(self.events) if not e.get("asset_external_id") or e["asset_external_id"] in ids]
        files = [f for f in keep(self.files) if not f.get("asset_external_id") or f["asset_external_id"] in ids]
        return Catalog(
            assets=assets,
            timeseries=ts,
            events=events,
            files=files,
            relationships=[
                r
                for r in self.relationships
                if r.get("source_external_id") in ids or r.get("target_external_id") in ids
            ],
            batches=self.batches if industry == "pharma" else [],
            counts=self.counts,
            project=self.project,
            space=self.space,
            model=self.model,
        )


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
    return {
        "timeseries": [t for t in catalog.timeseries if t.get("asset_external_id") in scope],
        "events": [e for e in catalog.events if e.get("asset_external_id") in scope],
        "files": [f for f in catalog.files if f.get("asset_external_id") in scope],
        "relationships": [
            r
            for r in catalog.relationships
            if r.get("source_external_id") in scope or r.get("target_external_id") in scope
        ],
    }


def context_pack(catalog: Catalog, asset: dict, industry: str) -> dict:
    related = related_rows(catalog, asset["external_id"])
    return {
        "project": catalog.project,
        "space": catalog.space,
        "data_model": catalog.model,
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
