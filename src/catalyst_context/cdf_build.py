"""Local CDF data-model and transformation-job definitions (not auto-deployed)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CDF_DIR = ROOT / "cdf"
MODULE_DIR = ROOT / "modules" / "catalyst_context"

DATA_MODEL = {
    "space": "catalyst_context",
    "external_id": "CatalystContext",
    "version": "v1",
    "name": "Catalyst Context",
    "status": "defined in modules/catalyst_context — run scripts/deploy_cdf.py or cdf deploy",
    "containers": (
        {"external_id": "Site", "used_for": "node", "purpose": "ISA-95 site / O&G field"},
        {"external_id": "Equipment", "used_for": "node", "purpose": "Unit, equipment module, rotating equipment"},
        {"external_id": "ProcessSignal", "used_for": "node", "purpose": "Historian tag linked to equipment"},
        {"external_id": "ProcessEvent", "used_for": "node", "purpose": "Deviation, alarm, well perturbation, work order"},
        {"external_id": "EngineeringFile", "used_for": "node", "purpose": "P&ID, eBR, datasheet, CoA"},
        {"external_id": "Batch", "used_for": "node", "purpose": "ISA-88 batch instance (pharma)"},
        {"external_id": "QualityResult", "used_for": "node", "purpose": "LIMS / CoA result linked to batch"},
    ),
    "views": (
        {"external_id": "Site", "purpose": "ISA-95 site / O&G field or installation"},
        {"external_id": "Equipment", "purpose": "Unit, equipment module, rotating equipment"},
        {"external_id": "ProcessSignal", "purpose": "Historian tag linked to equipment"},
        {"external_id": "ProcessEvent", "purpose": "Deviation, alarm, well perturbation, work order"},
        {"external_id": "EngineeringFile", "purpose": "P&ID, eBR, datasheet, CoA"},
        {"external_id": "Batch", "purpose": "ISA-88 batch instance (pharma)"},
        {"external_id": "QualityResult", "purpose": "LIMS / CoA result linked to batch"},
    ),
}

TRANSFORMATION_JOBS = (
    {
        "external_id": "tr-catalyst-raw-to-sites",
        "name": "RAW equipment → Site instances",
        "source": "RAW catalyst_context_raw.equipment (kind Site/Field)",
        "destination": "Data model CatalystContext.Site",
        "file": "modules/catalyst_context/transformations/tr_catalyst_raw_to_sites.sql",
    },
    {
        "external_id": "tr-catalyst-raw-to-equipment",
        "name": "RAW equipment → Equipment instances",
        "source": "RAW catalyst_context_raw.equipment",
        "destination": "Data model CatalystContext.Equipment",
        "file": "modules/catalyst_context/transformations/tr_catalyst_raw_to_equipment.sql",
    },
    {
        "external_id": "tr-catalyst-raw-to-signals",
        "name": "RAW tags → ProcessSignal instances",
        "source": "RAW catalyst_context_raw.timeseries",
        "destination": "Data model CatalystContext.ProcessSignal",
        "file": "modules/catalyst_context/transformations/tr_catalyst_raw_to_signals.sql",
    },
    {
        "external_id": "tr-catalyst-raw-to-events",
        "name": "RAW events → ProcessEvent instances",
        "source": "RAW catalyst_context_raw.events",
        "destination": "Data model CatalystContext.ProcessEvent",
        "file": "modules/catalyst_context/transformations/tr_catalyst_raw_to_events.sql",
    },
)


def artifact_paths() -> dict[str, Path]:
    dm = MODULE_DIR / "data_modeling"
    raw = MODULE_DIR / "raw"
    return {
        "space": dm / "catalyst_context.Space.yaml",
        "datamodel": dm / "CatalystContext.DataModel.yaml",
        "site_container": dm / "containers" / "1.Site.Container.yaml",
        "site_view": dm / "views" / "1.Site.View.yaml",
        "graphql": CDF_DIR / "data_models" / "CatalystContext.graphql",
        "raw_equipment": raw / "equipment.Table.csv",
        "raw_timeseries": raw / "timeseries.Table.csv",
        "raw_events": raw / "events.Table.csv",
    }


def artifacts_present() -> bool:
    return all(path.exists() for path in artifact_paths().values())
