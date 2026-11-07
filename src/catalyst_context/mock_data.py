"""Demo catalog patterned on Cognite ISA-88/95 and Open Industrial Data (Valhall compressor)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _asset(
    external_id: str,
    name: str,
    description: str,
    parent: str | None,
    industry: str,
    kind: str,
    metadata: dict[str, str],
) -> dict:
    return {
        "id": abs(hash(external_id)) % 10_000_000,
        "external_id": external_id,
        "name": name,
        "description": description,
        "parent_external_id": parent,
        "industry": industry,
        "kind": kind,
        "metadata": metadata,
    }


def _ts(external_id: str, name: str, asset: str, unit: str, industry: str) -> dict:
    return {
        "id": abs(hash(external_id)) % 10_000_000,
        "external_id": external_id,
        "name": name,
        "asset_external_id": asset,
        "unit": unit,
        "industry": industry,
    }


def _event(
    external_id: str,
    type_: str,
    subtype: str,
    description: str,
    asset: str,
    hours_ago: int,
    industry: str,
) -> dict:
    end = _now() - timedelta(hours=hours_ago)
    start = end - timedelta(hours=2)
    return {
        "external_id": external_id,
        "type": type_,
        "subtype": subtype,
        "description": description,
        "asset_external_id": asset,
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
        "industry": industry,
    }


def _file(external_id: str, name: str, mime: str, asset: str, industry: str) -> dict:
    return {
        "external_id": external_id,
        "name": name,
        "mime_type": mime,
        "asset_external_id": asset,
        "industry": industry,
    }


def _rel(source: str, target: str, rel_type: str) -> dict:
    return {"source_external_id": source, "target_external_id": target, "type": rel_type}


def pharma_assets() -> list[dict]:
    return [
        _asset("pharma-site-helix", "Helix Park Biologics", "Drug substance site (ISA-95 Site)", None, "pharma", "Site", {"standard": "ISA-95"}),
        _asset("pharma-area-usp", "USP Suite A", "Upstream process area", "pharma-site-helix", "pharma", "Area", {"process": "upstream"}),
        _asset("pharma-cell-brx", "Process cell BRX-04", "Fed-batch mammalian cell culture", "pharma-area-usp", "pharma", "ProcessCell", {"isa88": "unit"}),
        _asset("pharma-unit-bioreactor", "Bioreactor BRX-04", "2000 L stainless bioreactor", "pharma-cell-brx", "pharma", "Unit", {"volume_l": "2000"}),
        _asset("pharma-eq-agitator", "Agitator AG-04", "Impeller and drive", "pharma-unit-bioreactor", "pharma", "EquipmentModule", {"criticality": "high"}),
        _asset("pharma-area-dsp", "DSP Suite B", "Downstream purification", "pharma-site-helix", "pharma", "Area", {"process": "downstream"}),
        _asset("pharma-unit-chromatography", "Chromatography skid CHR-12", "Protein A capture", "pharma-area-dsp", "pharma", "Unit", {"phase": "capture"}),
        _asset("pharma-unit-ufdf", "UF/DF skid UF-07", "Ultrafiltration / diafiltration", "pharma-area-dsp", "pharma", "Unit", {"phase": "formulation"}),
        _asset("pharma-lab-qc", "QC lab LIMS", "In-process and release testing", "pharma-site-helix", "pharma", "Area", {"system": "LIMS"}),
    ]


def oil_gas_assets() -> list[dict]:
    return [
        _asset("og-field-harbor", "Harbor Ridge Field", "Offshore production analog (Open Industrial Data pattern)", None, "oil_gas", "Field", {"region": "NCS analog"}),
        _asset("og-inst-platform", "Harbor Ridge Platform", "Manned installation", "og-field-harbor", "oil_gas", "Installation", {"manned": "true"}),
        _asset("og-sys-compression", "1st stage compression", "Export gas compression train", "og-inst-platform", "oil_gas", "System", {"train": "1"}),
        _asset("og-eq-suction-cooler", "1st stage suction cooler", "Gas cooling upstream of scrubber", "og-sys-compression", "oil_gas", "Equipment", {"pid": "PID-4101"}),
        _asset("og-eq-scrubber", "1st stage suction scrubber", "Liquid knockout", "og-sys-compression", "oil_gas", "Equipment", {"pid": "PID-4101"}),
        _asset("og-eq-compressor", "1st stage compressor K-4101", "Centrifugal compressor", "og-sys-compression", "oil_gas", "Equipment", {"criticality": "A"}),
        _asset("og-eq-discharge-cooler", "1st stage discharge cooler", "Aftercooler", "og-sys-compression", "oil_gas", "Equipment", {"pid": "PID-4102"}),
        _asset("og-eq-export-pump", "Multiphase export pump P-2208", "Rotating equipment analog (Mittelplate-style)", "og-inst-platform", "oil_gas", "Equipment", {"service": "export"}),
    ]


def pharma_timeseries() -> list[dict]:
    return [
        _ts("pharma.ts.brx.do", "Dissolved oxygen", "pharma-unit-bioreactor", "%", "pharma"),
        _ts("pharma.ts.brx.ph", "Culture pH", "pharma-unit-bioreactor", "pH", "pharma"),
        _ts("pharma.ts.brx.temp", "Jacket temperature", "pharma-unit-bioreactor", "°C", "pharma"),
        _ts("pharma.ts.brx.agitation", "Agitation speed", "pharma-eq-agitator", "rpm", "pharma"),
        _ts("pharma.ts.chr.pressure", "Column delta-P", "pharma-unit-chromatography", "bar", "pharma"),
        _ts("pharma.ts.chr.uv", "UV 280 nm", "pharma-unit-chromatography", "mAU", "pharma"),
        _ts("pharma.ts.uf.flux", "UF flux", "pharma-unit-ufdf", "LMH", "pharma"),
    ]


def oil_gas_timeseries() -> list[dict]:
    return [
        _ts("og.ts.k4101.vib", "Compressor vibration", "og-eq-compressor", "mm/s", "oil_gas"),
        _ts("og.ts.k4101.suction-p", "Suction pressure", "og-eq-compressor", "bar", "oil_gas"),
        _ts("og.ts.k4101.discharge-p", "Discharge pressure", "og-eq-compressor", "bar", "oil_gas"),
        _ts("og.ts.k4101.bearing-t", "Bearing temperature", "og-eq-compressor", "°C", "oil_gas"),
        _ts("og.ts.cooler.out-t", "Suction cooler outlet T", "og-eq-suction-cooler", "°C", "oil_gas"),
        _ts("og.ts.pump.vib", "Export pump vibration", "og-eq-export-pump", "mm/s", "oil_gas"),
        _ts("og.ts.well.cgr", "Condensate-gas ratio", "og-field-harbor", "stb/MMscf", "oil_gas"),
    ]


def pharma_events() -> list[dict]:
    return [
        _event("pharma.evt.batch-start", "Batch", "PhaseStart", "Batch HP-DS-24018 inoculation", "pharma-unit-bioreactor", 96, "pharma"),
        _event("pharma.evt.do-excursion", "Deviation", "Process", "DO dropped below 30% for 18 minutes", "pharma-unit-bioreactor", 40, "pharma"),
        _event("pharma.evt.qc-fail", "QualityResult", "OOS", "Endotoxin OOS on in-process sample", "pharma-lab-qc", 12, "pharma"),
        _event("pharma.evt.golden", "Batch", "Golden", "Reference golden batch HP-DS-23991", "pharma-unit-bioreactor", 720, "pharma"),
    ]


def oil_gas_events() -> list[dict]:
    return [
        _event("og.evt.high-vib", "Alarm", "Condition", "Compressor vibration above advisory", "og-eq-compressor", 8, "oil_gas"),
        _event("og.evt.well-perturb", "Production", "WellPerturbation", "Well test window for CGR/WGR back-allocation", "og-field-harbor", 30, "oil_gas"),
        _event("og.evt.wo", "Maintenance", "WorkOrder", "Inspect K-4101 thrust bearing", "og-eq-compressor", 4, "oil_gas"),
        _event("og.evt.pump-seal", "Alarm", "Integrity", "Export pump seal leak rate rising", "og-eq-export-pump", 20, "oil_gas"),
    ]


def pharma_files() -> list[dict]:
    return [
        _file("pharma.file.pfd", "USP_SuiteA_PFD.pdf", "application/pdf", "pharma-area-usp", "pharma"),
        _file("pharma.file.recipe", "Recipe_FedBatch_mAb.xlsx", "application/vnd.ms-excel", "pharma-unit-bioreactor", "pharma"),
        _file("pharma.file.batch-record", "eBR_HP-DS-24018.pdf", "application/pdf", "pharma-unit-bioreactor", "pharma"),
        _file("pharma.file.coa", "CoA_lot_HP-DS-24018.pdf", "application/pdf", "pharma-lab-qc", "pharma"),
    ]


def oil_gas_files() -> list[dict]:
    return [
        _file("og.file.pid-4101", "PID-4101_1st_stage_compression.pdf", "application/pdf", "og-sys-compression", "oil_gas"),
        _file("og.file.pid-4102", "PID-4102_discharge_cooler.pdf", "application/pdf", "og-eq-discharge-cooler", "oil_gas"),
        _file("og.file.datasheet", "K-4101_compressor_datasheet.pdf", "application/pdf", "og-eq-compressor", "oil_gas"),
        _file("og.file.wo", "WO-88421_bearing_inspect.pdf", "application/pdf", "og-eq-compressor", "oil_gas"),
    ]


def relationships() -> list[dict]:
    return [
        _rel("pharma-unit-bioreactor", "pharma.ts.brx.do", "belongs_to"),
        _rel("pharma-unit-bioreactor", "pharma.file.batch-record", "documented_by"),
        _rel("pharma.evt.do-excursion", "pharma.ts.brx.do", "evidenced_by"),
        _rel("pharma.evt.qc-fail", "pharma-unit-bioreactor", "impacts"),
        _rel("og-eq-compressor", "og.ts.k4101.vib", "belongs_to"),
        _rel("og-eq-compressor", "og.file.pid-4101", "documented_by"),
        _rel("og.evt.high-vib", "og.ts.k4101.vib", "evidenced_by"),
        _rel("og.evt.wo", "og.file.wo", "documented_by"),
    ]


def batches() -> list[dict]:
    return [
        {
            "batch_id": "HP-DS-23991",
            "recipe": "FedBatch_mAb_v4",
            "status": "Golden",
            "yield_pct": 94.2,
            "cycle_h": 268,
            "deviations": 0,
        },
        {
            "batch_id": "HP-DS-24018",
            "recipe": "FedBatch_mAb_v4",
            "status": "In review",
            "yield_pct": 87.1,
            "cycle_h": 281,
            "deviations": 2,
        },
        {
            "batch_id": "HP-DS-24011",
            "recipe": "FedBatch_mAb_v4",
            "status": "Released",
            "yield_pct": 91.4,
            "cycle_h": 272,
            "deviations": 1,
        },
    ]


TS_GENERATORS = {
    "pharma.ts.brx.do": lambda t: 40 + 8 * np.sin(t / 6) + np.where((t > 70) & (t < 78), -14, 0),
    "pharma.ts.brx.ph": lambda t: 7.05 + 0.08 * np.sin(t / 10),
    "pharma.ts.brx.temp": lambda t: 36.8 + 0.25 * np.sin(t / 8),
    "pharma.ts.brx.agitation": lambda t: 80 + 4 * np.sin(t / 20),
    "pharma.ts.chr.pressure": lambda t: 1.1 + 0.15 * (t / 160) + 0.05 * np.sin(t / 4),
    "pharma.ts.chr.uv": lambda t: 120 + 80 * np.exp(-((t - 90) ** 2) / 40),
    "pharma.ts.uf.flux": lambda t: 42 - 0.08 * t + 2 * np.sin(t / 12),
    "og.ts.k4101.vib": lambda t: 3.2 + 0.4 * np.sin(t / 5) + np.where(t > 140, 2.8, 0),
    "og.ts.k4101.suction-p": lambda t: 18.4 + 0.6 * np.sin(t / 9),
    "og.ts.k4101.discharge-p": lambda t: 62 + 1.2 * np.sin(t / 9),
    "og.ts.k4101.bearing-t": lambda t: 71 + 0.08 * t / 10 + np.where(t > 140, 6, 0),
    "og.ts.cooler.out-t": lambda t: 28 + 1.5 * np.sin(t / 14),
    "og.ts.pump.vib": lambda t: 2.1 + 0.3 * np.sin(t / 7) + np.where((t > 100) & (t < 120), 1.6, 0),
    "og.ts.well.cgr": lambda t: 42 + 3 * np.sin(t / 18) + np.where((t > 50) & (t < 60), 8, 0),
}


def datapoints(external_id: str, hours: int = 168) -> pd.DataFrame:
    rng = np.random.default_rng(abs(hash(external_id)) % 10_000)
    index = pd.date_range(_now() - timedelta(hours=hours), periods=hours, freq="h", tz="UTC")
    t = np.arange(hours, dtype=float)
    fn = TS_GENERATORS.get(external_id, lambda x: 10 + np.sin(x / 8))
    values = np.asarray(fn(t), dtype=float) + rng.normal(0, 0.15, size=hours)
    return pd.DataFrame({external_id: values}, index=index)


@dataclass
class Catalog:
    assets: list[dict] = field(default_factory=list)
    timeseries: list[dict] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    files: list[dict] = field(default_factory=list)
    relationships: list[dict] = field(default_factory=list)
    batches: list[dict] = field(default_factory=list)
    mode: str = "demo"
    project: str = "demo-catalyst-context"

    def filter_industry(self, industry: str) -> "Catalog":
        if industry == "both" or self.mode == "live":
            return self

        def keep(rows: list[dict]) -> list[dict]:
            return [r for r in rows if r.get("industry") in {industry, None}]

        asset_ids = {a["external_id"] for a in keep(self.assets)}
        ts = [t for t in keep(self.timeseries) if t["asset_external_id"] in asset_ids or t.get("industry") == industry]
        return Catalog(
            assets=keep(self.assets),
            timeseries=ts,
            events=keep(self.events),
            files=keep(self.files),
            relationships=[
                r
                for r in self.relationships
                if r["source_external_id"] in asset_ids
                or r["target_external_id"] in asset_ids
                or any(r["source_external_id"] == t["external_id"] or r["target_external_id"] == t["external_id"] for t in ts)
            ],
            batches=self.batches if industry == "pharma" else [],
            mode=self.mode,
            project=self.project,
        )


def demo_catalog() -> Catalog:
    return Catalog(
        assets=pharma_assets() + oil_gas_assets(),
        timeseries=pharma_timeseries() + oil_gas_timeseries(),
        events=pharma_events() + oil_gas_events(),
        files=pharma_files() + oil_gas_files(),
        relationships=relationships(),
        batches=batches(),
        mode="demo",
        project="demo-catalyst-context",
    )
