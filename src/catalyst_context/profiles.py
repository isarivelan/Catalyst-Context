"""Industry lenses that shape labels, KPIs, and recommended CDF objects."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IndustryProfile:
    key: str
    title: str
    audience: str
    promise: str
    hierarchy: tuple[str, ...]
    kpis: tuple[str, ...]
    sources: tuple[str, ...]
    cdf_objects: tuple[str, ...]
    use_cases: tuple[str, ...]


PHARMA = IndustryProfile(
    key="pharma",
    title="Life sciences manufacturing",
    audience="Process, quality, and MSAT teams",
    promise="Golden-batch comparison, deviation context, and lot traceability on one graph.",
    hierarchy=(
        "Enterprise",
        "Site",
        "Area",
        "Process cell",
        "Unit",
        "Equipment module",
    ),
    kpis=("Batch yield", "Deviation rate", "OEE", "Cycle time vs recipe"),
    sources=("Historian / MQTT", "MES", "LIMS", "SAP / ERP", "Veeva / batch docs"),
    cdf_objects=(
        "Assets (ISA-95 units)",
        "Time series (ISATimeSeries)",
        "Events (phases, deviations)",
        "Files (batch records, SOPs)",
        "QualityResult / MaterialLot",
    ),
    use_cases=(
        "Identify a golden batch against recipe limits",
        "Link a quality fail to the unit, phase, and sensor trend",
        "Give MSAT a site twin without hopping MES → LIMS → historian",
    ),
)

OIL_GAS = IndustryProfile(
    key="oil_gas",
    title="Oil and gas operations",
    audience="Production, rotating equipment, and integrity teams",
    promise="Live process context on critical rotating equipment, P&IDs, and production events.",
    hierarchy=("Field", "Installation", "System", "Equipment", "Tag"),
    kpis=("Uptime", "MTBF", "CGR / WGR allocation", "Condition alerts"),
    sources=("OSIsoft PI / historian", "CMMS", "P&IDs", "HYSYS / models", "Work orders"),
    cdf_objects=(
        "Assets (equipment hierarchy)",
        "Time series (vibration, T, P, flow)",
        "Events (alarms, well perturbations)",
        "Files (P&IDs, datasheets)",
        "Relationships (tag ↔ document ↔ sensor)",
    ),
    use_cases=(
        "Condition monitoring on a compressor / pump train",
        "Overlay live tags on a P&ID without leaving the app",
        "Cut time-to-context for production and maintenance engineers",
    ),
)

BOTH = IndustryProfile(
    key="both",
    title="Process industries (pharma + energy)",
    audience="Digital, operations, and reliability programs",
    promise="One contextualization pattern: asset → signal → event → document, reused across sites.",
    hierarchy=("Site", "Area / system", "Unit / equipment", "Tag"),
    kpis=("Time-to-context", "Unplanned downtime", "Quality / allocation exceptions"),
    sources=("Historians", "CMMS / MES", "LIMS or lab", "Engineering files", "ERP"),
    cdf_objects=("Assets", "Time series", "Events", "Files", "Relationships"),
    use_cases=(
        "Same Streamlit flow, industry-specific language and KPIs",
        "Prove CDF contextualization before a full industrial AI rollout",
        "Scale a use case from one site to a fleet",
    ),
)

PROFILES = {p.key: p for p in (PHARMA, OIL_GAS, BOTH)}

FLOW_STEPS = (
    ("lens", "Industry lens"),
    ("connect", "Connect"),
    ("site", "Site graph"),
    ("signals", "Process signals"),
    ("integrity", "Quality & integrity"),
    ("context", "Context pack"),
)
