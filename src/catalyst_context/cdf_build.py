"""Local CDF data-model and transformation-job definitions (not auto-deployed)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CDF_DIR = ROOT / "cdf"

DATA_MODEL = {
    "space": "catalyst_context",
    "external_id": "CatalystContext",
    "version": "v1",
    "name": "Catalyst Context",
    "status": "defined in repo — run scripts/deploy_cdf.py to publish into your CDF project",
    "views": (
        {"external_id": "Site", "purpose": "ISA-95 site / O&G field or installation"},
        {"external_id": "Equipment", "purpose": "Unit, equipment module, rotating equipment"},
        {"external_id": "ProcessSignal", "purpose": "Historian tag linked to equipment"},
        {"external_id": "Batch", "purpose": "ISA-88 batch instance (pharma)"},
        {"external_id": "QualityResult", "purpose": "LIMS / CoA result linked to batch"},
        {"external_id": "ProcessEvent", "purpose": "Deviation, alarm, well perturbation, work order"},
        {"external_id": "EngineeringFile", "purpose": "P&ID, eBR, datasheet, CoA"},
    ),
}

TRANSFORMATION_JOBS = (
    {
        "external_id": "tr-catalyst-raw-to-equipment",
        "name": "RAW equipment → Equipment instances",
        "source": "RAW catalyst_context_raw.equipment",
        "destination": "Data model CatalystContext.Equipment",
        "file": "cdf/transformations/tr_raw_to_equipment.sql",
    },
    {
        "external_id": "tr-catalyst-raw-to-signals",
        "name": "RAW tags → ProcessSignal instances",
        "source": "RAW catalyst_context_raw.timeseries",
        "destination": "Data model CatalystContext.ProcessSignal",
        "file": "cdf/transformations/tr_raw_to_signals.sql",
    },
    {
        "external_id": "tr-catalyst-raw-to-events",
        "name": "RAW events → ProcessEvent instances",
        "source": "RAW catalyst_context_raw.events",
        "destination": "Data model CatalystContext.ProcessEvent",
        "file": "cdf/transformations/tr_raw_to_events.sql",
    },
)


def artifact_paths() -> dict[str, Path]:
    return {
        "graphql": CDF_DIR / "data_models" / "CatalystContext.graphql",
        "datamodel": CDF_DIR / "data_models" / "datamodel.yaml",
        "raw_equipment": CDF_DIR / "raw" / "equipment.csv",
        "raw_timeseries": CDF_DIR / "raw" / "timeseries.csv",
        "raw_events": CDF_DIR / "raw" / "events.csv",
    }


def artifacts_present() -> bool:
    return all(path.exists() for path in artifact_paths().values())
