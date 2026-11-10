"""Industry lenses that shape labels in the Streamlit flow."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IndustryProfile:
    key: str
    title: str
    promise: str
    hierarchy: tuple[str, ...]
    sources: tuple[str, ...]
    use_cases: tuple[str, ...]


PHARMA = IndustryProfile(
    key="pharma",
    title="Life sciences manufacturing",
    promise="Golden-batch comparison, deviation context, and lot traceability on one graph.",
    hierarchy=("Site", "Area", "Process cell", "Unit", "Equipment module"),
    sources=("Historian", "MES", "LIMS", "SAP / ERP", "Batch docs"),
    use_cases=(
        "Identify a golden batch against recipe limits",
        "Link a quality fail to the unit, phase, and sensor trend",
        "Give MSAT a site twin without hopping MES → LIMS → historian",
    ),
)

OIL_GAS = IndustryProfile(
    key="oil_gas",
    title="Oil and gas operations",
    promise="Live process context on critical rotating equipment, P&IDs, and production events.",
    hierarchy=("Field", "Installation", "System", "Equipment", "Tag"),
    sources=("PI / historian", "CMMS", "P&IDs", "Work orders"),
    use_cases=(
        "Condition monitoring on a compressor / pump train",
        "Overlay live tags on a P&ID without leaving the app",
        "Cut time-to-context for production and maintenance engineers",
    ),
)

BOTH = IndustryProfile(
    key="both",
    title="Process industries (pharma + energy)",
    promise="One contextualization pattern: equipment → signal → event → document.",
    hierarchy=("Site", "Area / system", "Unit / equipment", "Tag"),
    sources=("Historians", "CMMS / MES", "LIMS", "Engineering files"),
    use_cases=(
        "Same Streamlit flow, industry-specific language",
        "Prove CDF contextualization on the CatalystContext model",
        "Scale a use case from one site to a fleet",
    ),
)

PROFILES = {p.key: p for p in (PHARMA, OIL_GAS, BOTH)}

FLOW_STEPS = (
    ("lens", "Industry lens"),
    ("model", "Data model"),
    ("site", "Site graph"),
    ("signals", "Process signals"),
    ("integrity", "Quality & integrity"),
    ("context", "Context pack"),
)
