"""Atlas AI agent for Catalyst Context."""

from __future__ import annotations

from typing import Any

ATLAS_AGENT_ID = "catalyst-context-atlas"
ATLAS_AGENT_NAME = "Catalyst Context Atlas"

INSTRUCTIONS = (
    "You are Atlas AI for the Catalyst Context app. Answer from the CatalystContext "
    "data model in space catalyst_context: Site, Equipment, ProcessSignal, ProcessEvent, "
    "EngineeringFile, Batch, and QualityResult. Help with golden-batch comparison "
    "(HP-DS-23991 vs HP-DS-24018), deviations, files linked to equipment, and time series. "
    "Be concise and name the equipment or batch you used."
)


def atlas_agent_upsert():
    from cognite.client.data_classes.agents import AgentUpsert
    from cognite.client.data_classes.agents.agent_tools import (
        DataModelInfo,
        InstanceSpaces,
        QueryKnowledgeGraphAgentToolConfiguration,
        QueryKnowledgeGraphAgentToolUpsert,
        QueryTimeSeriesDatapointsAgentToolUpsert,
        SummarizeDocumentAgentToolUpsert,
    )

    from catalyst_context import MODEL_ID, MODEL_VERSION, SPACE, VIEWS

    kg = QueryKnowledgeGraphAgentToolUpsert(
        name="query_catalyst_context",
        description="Query Site, Equipment, ProcessSignal, ProcessEvent, EngineeringFile, Batch, and QualityResult.",
        configuration=QueryKnowledgeGraphAgentToolConfiguration(
            data_models=[
                DataModelInfo(
                    space=SPACE,
                    external_id=MODEL_ID,
                    version=MODEL_VERSION,
                    view_external_ids=list(VIEWS),
                )
            ],
            instance_spaces=InstanceSpaces(type="manual", spaces=[SPACE]),
        ),
    )
    ts_tool = QueryTimeSeriesDatapointsAgentToolUpsert(
        name="query_timeseries",
        description="Retrieve historian datapoints for ProcessSignal externalTag values.",
    )
    docs = SummarizeDocumentAgentToolUpsert(
        name="summarize_files",
        description="Summarize engineering files linked to equipment (P&ID, eBR, CoA, SOP).",
    )
    return AgentUpsert(
        external_id=ATLAS_AGENT_ID,
        name=ATLAS_AGENT_NAME,
        description="Process-industry context assistant on CatalystContext v1.",
        instructions=INSTRUCTIONS,
        labels=["published"],
        tools=[kg, ts_tool, docs],
    )


def ensure_atlas_agent(client) -> tuple[bool, str]:
    agent = atlas_agent_upsert()
    try:
        client.agents.upsert(agent)
        return True, ATLAS_AGENT_ID
    except Exception as exc:
        try:
            agent.tools = [tool for tool in (agent.tools or []) if getattr(tool, "_type", "") != "summarizeDocument"]
            client.agents.upsert(agent)
            return True, ATLAS_AGENT_ID
        except Exception:
            return False, f"{type(exc).__name__}: {exc}"


def atlas_chat(client, text: str, cursor: str | None = None) -> tuple[str, str | None]:
    from cognite.client.data_classes.agents import Message

    response = client.agents.chat(
        agent_external_id=ATLAS_AGENT_ID,
        messages=Message(text),
        cursor=cursor,
    )
    reply = response.text or "Atlas returned no text."
    return reply, getattr(response, "cursor", None)


def catalog_fallback(catalog: Any, question: str) -> str:
    q = question.lower()
    lines = [
        "Atlas AI was not available, so this answer uses CatalystContext instances already loaded in the app.",
        "",
    ]
    if any(w in q for w in ("golden", "batch", "yield", "hp-ds")):
        if catalog.batches:
            lines.append("Batches:")
            for b in catalog.batches:
                lines.append(
                    f"- {b.get('batch_id')} · {b.get('status')} · yield {b.get('yield_pct')}% · "
                    f"{b.get('cycle_h')} h · deviations {b.get('deviations')} · unit {b.get('unit')}"
                )
        else:
            lines.append("No Batch instances in this lens.")
    if any(w in q for w in ("file", "p&id", "ebr", "coa", "sop", "document")):
        lines.append("Engineering files:")
        for f in catalog.files[:12]:
            lines.append(f"- {f.get('name')} ({f.get('kind')}) → {f.get('asset_external_id')}")
    if any(w in q for w in ("deviat", "event", "oos", "alarm")):
        lines.append("Events:")
        for e in catalog.events[:10]:
            lines.append(f"- {e.get('subtype') or e.get('type')}: {e.get('description')}")
    if any(w in q for w in ("signal", "tag", "do", "pH", "temperature", "trend")):
        lines.append("Process signals:")
        for t in catalog.timeseries[:12]:
            lines.append(f"- {t.get('name')} ({t.get('unit')}) on {t.get('asset_external_id')}")
    if len(lines) == 2:
        lines.append(f"Equipment count: {len(catalog.assets)}. Signals: {len(catalog.timeseries)}. Files: {len(catalog.files)}.")
        if catalog.assets:
            lines.append("Sites / units: " + ", ".join(a["name"] for a in catalog.assets[:8]))
    return "\n".join(lines)
