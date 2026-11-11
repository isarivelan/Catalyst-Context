"""Catalyst Context — Streamlit app on the CatalystContext CDF data model.

Built to run in Fusion Flows (Pyodide/stlite) as well as locally.
Created by Isarivelan Mani.
"""

from __future__ import annotations

try:
    import pyodide_http

    pyodide_http.patch_all()
except Exception:
    pass

import pandas as pd
import streamlit as st

try:
    import plotly.express as px
    import plotly.graph_objects as go

    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from catalyst_context import MODEL_ID, MODEL_VERSION, SPACE, VIEWS
from catalyst_context.catalog import (
    children,
    context_pack,
    pack_json,
    related_rows,
    roots,
    timeseries_csv,
)
from catalyst_context.atlas import (
    ATLAS_AGENT_ID,
    ATLAS_AGENT_NAME,
    atlas_chat,
    catalog_fallback,
    ensure_atlas_agent,
)
from catalyst_context.client import get_client, load_model_catalog, signal_frame, synthetic_frame
from catalyst_context.profiles import FLOW_STEPS, PROFILES

st.set_page_config(page_title="Catalyst Context", layout="wide", initial_sidebar_state="expanded")

STEP_KEYS = [k for k, _ in FLOW_STEPS]
CREATOR = "Isarivelan Mani"

CSS = """
<style>
html, body, [class*="css"] { font-family: Source Sans 3, Segoe UI, sans-serif; }
[data-testid="stHeader"] { background: transparent; height: 0; }
.block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1180px; }
[data-testid="stSidebar"] { background: #1c1917 !important; }
[data-testid="stSidebar"] * { color: #fafaf9 !important; }
[data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color: #d6d3d1 !important; }
[data-testid="stSidebar"] button {
  background: #292524 !important;
  color: #fafaf9 !important;
  border: 1px solid #57534e !important;
  text-align: left !important;
  justify-content: flex-start !important;
}
[data-testid="stSidebar"] button p { color: #fafaf9 !important; }
[data-testid="stSidebar"] button[kind="primary"] {
  background: #0f766e !important;
  border-color: #14b8a6 !important;
  color: #ecfdf5 !important;
}
[data-testid="stSidebar"] button[kind="primary"] p { color: #ecfdf5 !important; }
.brand-mark { font-size: 0.72rem; letter-spacing: 0.22em; text-transform: uppercase; color: #d6d3d1; font-weight: 600; }
.brand-title { font-size: 1.35rem; margin: 0.2rem 0 0.35rem 0; color: #fffbeb; font-weight: 700; }
.hero-kicker { letter-spacing: 0.18em; text-transform: uppercase; color: #0f766e; font-size: 0.75rem; font-weight: 700; }
.hero-title { font-size: 2rem; font-weight: 700; margin: 0.2rem 0 0.4rem 0; line-height: 1.15; color: #1c1917; }
.hero-sub { color: #57534e; font-size: 1.05rem; margin-bottom: 1.2rem; max-width: 46rem; }
.kpi { background: #fffcf7; border: 1px solid #e7e5e4; border-radius: 14px; padding: 0.9rem 1rem; }
.kpi .label { color: #78716c; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; }
.kpi .value { font-size: 1.45rem; font-weight: 700; color: #1c1917; }
.card { border: 1px solid #e7e5e4; border-radius: 16px; padding: 1.1rem 1.15rem; background: #fffcf7; min-height: 8rem; }
.card h4 { margin: 0 0 0.4rem 0; font-size: 1.2rem; }
.card p { color: #57534e; margin: 0; line-height: 1.45; }
.chip { display: inline-block; background: #ecfdf5; color: #115e59; border-radius: 999px; padding: 0.15rem 0.6rem; font-size: 0.75rem; font-weight: 600; margin-bottom: 0.55rem; }
.event { border-left: 4px solid #0f766e; background: #fffcf7; border-radius: 0 12px 12px 0; padding: 0.7rem 0.9rem; margin-bottom: 0.55rem; border: 1px solid #e7e5e4; }
.event.warn { border-left-color: #d97706; }
.event.bad { border-left-color: #b91c1c; }
.event .meta { color: #78716c; font-size: 0.78rem; }
.pipe { display: flex; gap: 0.5rem; flex-wrap: wrap; margin: 0.6rem 0 1.1rem 0; }
.pipe span { background: #1c1917; color: #fffbeb; border-radius: 999px; padding: 0.35rem 0.8rem; font-size: 0.82rem; }
.pipe em { background: transparent; color: #78716c; font-style: normal; padding: 0.35rem 0.1rem; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def init_state() -> None:
    st.session_state.setdefault("step", "lens")
    st.session_state.setdefault("industry", "both")
    st.session_state.setdefault("client", None)
    st.session_state.setdefault("selected_asset", None)
    st.session_state.setdefault("atlas_messages", [])
    st.session_state.setdefault("atlas_cursor", None)
    st.session_state.setdefault("atlas_ready", None)


def goto(step: str) -> None:
    st.session_state.step = step
    st.rerun()


def client():
    if st.session_state.client is None:
        st.session_state.client = get_client()
    return st.session_state.client


def catalog():
    if "raw_catalog" not in st.session_state:
        with st.spinner("Loading CatalystContext instances…"):
            st.session_state.raw_catalog = load_model_catalog(client())
    return st.session_state.raw_catalog.filter_industry(st.session_state.industry)


def kpis(items: list[tuple[str, str | int]]) -> None:
    cols = st.columns(len(items))
    for col, (label, value) in zip(cols, items):
        col.markdown(
            f'<div class="kpi"><div class="label">{label}</div><div class="value">{value}</div></div>',
            unsafe_allow_html=True,
        )


def sidebar() -> None:
    with st.sidebar:
        st.markdown('<div class="brand-mark">CDF · CatalystContext v1</div>', unsafe_allow_html=True)
        st.markdown('<div class="brand-title">Catalyst Context</div>', unsafe_allow_html=True)
        st.caption(f"Created by {CREATOR}")
        current = st.session_state.step
        current_idx = STEP_KEYS.index(current)
        st.caption("Go to step")
        for i, (key, label) in enumerate(FLOW_STEPS):
            marker = "●" if key == current else ("✓" if i < current_idx else "○")
            if st.button(
                f"{marker}  {i + 1:02d}  {label}",
                key=f"nav_{key}",
                type="primary" if key == current else "secondary",
                use_container_width=True,
            ):
                if key != current:
                    goto(key)
        st.caption("Industry lens")
        st.write(PROFILES[st.session_state.industry].title)
        st.caption("Source")
        st.write(f"{SPACE} / {MODEL_ID} {MODEL_VERSION}")
        cols = st.columns(2)
        idx = current_idx
        if idx > 0 and cols[0].button("Back", use_container_width=True, key="nav_back"):
            goto(STEP_KEYS[idx - 1])
        if idx < len(STEP_KEYS) - 1 and cols[1].button("Next", use_container_width=True, type="primary", key="nav_next"):
            goto(STEP_KEYS[idx + 1])


def header(title: str, subtitle: str) -> None:
    st.markdown('<div class="hero-kicker">Catalyst Context</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="hero-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="hero-sub">{subtitle}</div>', unsafe_allow_html=True)


def step_lens() -> None:
    header(
        "One contextualization flow for process industries",
        "This app reads Site, Equipment, ProcessSignal, ProcessEvent, and related views from the CatalystContext data model.",
    )
    cols = st.columns(3)
    cards = [
        ("pharma", "Life sciences", "ISA-88/95 batch, LIMS, golden batch, deviations."),
        ("oil_gas", "Oil and gas", "Rotating equipment, P&IDs, PI historian, allocation."),
        ("both", "Shared pattern", "Equipment → signal → event → file. Reuse across sites."),
    ]
    for col, (key, title, body) in zip(cols, cards):
        selected = st.session_state.industry == key
        chip = "Selected" if selected else "Choose lens"
        with col:
            st.markdown(
                f'<div class="card"><div class="chip">{chip}</div><h4>{title}</h4><p>{body}</p></div>',
                unsafe_allow_html=True,
            )
            if st.button(
                f"Use {title}",
                key=f"pick_{key}",
                use_container_width=True,
                type="primary" if selected else "secondary",
            ):
                st.session_state.industry = key
                goto("model")


def step_model() -> None:
    header(
        "CatalystContext data model",
        f"Live instances in space `{SPACE}` · model `{MODEL_ID}` `{MODEL_VERSION}`.",
    )
    st.markdown(
        '<div class="pipe"><span>Space</span><em>→</em><span>Containers</span><em>→</em>'
        "<span>Views</span><em>→</em><span>This app</span></div>",
        unsafe_allow_html=True,
    )
    cat = catalog()
    counts = cat.counts
    kpis(
        [
            ("Project", cat.project or "—"),
            ("Site", counts.get("Site", 0)),
            ("Equipment", counts.get("Equipment", 0)),
            ("Signals", counts.get("ProcessSignal", 0)),
            ("Files", counts.get("EngineeringFile", 0)),
        ]
    )
    if sum(counts.values()) == 0:
        st.warning("The model is empty. Seed instances with `python scripts/deploy_cdf.py --seed-instances`.")
    st.dataframe(
        pd.DataFrame([{"view": name, "instances": counts.get(name, 0)} for name in VIEWS]),
        hide_index=True,
        use_container_width=True,
    )
    if st.button("Open site graph", type="primary"):
        goto("site")


def style_fig(fig, height: int = 400):
    fig.update_layout(
        height=height,
        margin=dict(t=28, l=10, r=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#fffcf7",
        font=dict(color="#1c1917", size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, title=""),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#e7e5e4", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#e7e5e4", zeroline=False)
    return fig


def hierarchy_figure(cat):
    labels = [a["name"] for a in cat.assets]
    ids = [a["external_id"] for a in cat.assets]
    name_by_ext = {a["external_id"]: a["name"] for a in cat.assets}
    parents = [
        name_by_ext.get(a.get("parent_external_id"), "") if a.get("parent_external_id") else ""
        for a in cat.assets
    ]
    fig = px.treemap(
        names=labels,
        parents=parents,
        ids=ids,
        color_discrete_sequence=["#0f766e", "#115e59", "#44403c", "#d6d3d1", "#f59e0b"],
    )
    return style_fig(fig, height=430)


def context_network(pack: dict):
    import math

    nodes = [("asset", pack["asset"]["name"])]
    nodes += [("ts", t["name"]) for t in pack["timeseries"][:6]]
    nodes += [("event", e.get("subtype") or e.get("type")) for e in pack["events"][:6]]
    nodes += [("file", (f.get("name") or "")[:28]) for f in pack["files"][:6]]
    n = max(len(nodes) - 1, 1)
    xs, ys, labels, colors = [0.0], [0.0], [nodes[0][1]], ["#0f766e"]
    palette = {"ts": "#0ea5e9", "event": "#d97706", "file": "#78716c"}
    for i, (kind, label) in enumerate(nodes[1:], start=1):
        angle = 2 * math.pi * (i - 1) / n
        xs.append(math.cos(angle))
        ys.append(math.sin(angle))
        labels.append(label)
        colors.append(palette.get(kind, "#a8a29e"))
    fig = go.Figure()
    for i in range(1, len(xs)):
        fig.add_trace(
            go.Scatter(
                x=[0, xs[i]],
                y=[0, ys[i]],
                mode="lines",
                line=dict(color="#d6d3d1", width=1.6),
                hoverinfo="skip",
                showlegend=False,
            )
        )
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="markers+text",
            text=labels,
            textposition="top center",
            marker=dict(size=[32] + [18] * (len(xs) - 1), color=colors, line=dict(width=0)),
            showlegend=False,
        )
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return style_fig(fig, height=430)


def asset_tree_table(cat) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "name": asset["name"],
                "kind": asset["kind"],
                "parent": asset.get("parent_external_id") or "—",
                "industry": asset.get("industry", ""),
            }
            for asset in cat.assets
        ]
    )


def step_site() -> None:
    cat = catalog()
    profile = PROFILES[st.session_state.industry]
    header("Site graph", f"{profile.hierarchy[0]} → {profile.hierarchy[-1]}  ·  {cat.model}")
    kpis(
        [
            ("Nodes", len(cat.assets)),
            ("ProcessSignal", len(cat.timeseries)),
            ("ProcessEvent", len(cat.events)),
            ("EngineeringFile", len(cat.files)),
        ]
    )
    left, right = st.columns((1, 1.4))
    with left:
        root_opts = roots(cat)
        if not root_opts:
            st.info("No Site/Equipment instances. Seed the data model, then refresh.")
            return
        root = st.selectbox("Root site / field", root_opts, format_func=lambda a: a["name"])
        level2 = children(cat, root["external_id"]) or [root]
        area = st.selectbox("Area / system", level2, format_func=lambda a: a["name"])
        level3 = children(cat, area["external_id"]) or [area]
        unit = st.selectbox("Unit / equipment", level3, format_func=lambda a: a["name"])
        st.session_state.selected_asset = unit
        st.markdown(f"**{unit['name']}**")
        st.caption(unit.get("description") or "")
    with right:
        if HAS_PLOTLY and cat.assets:
            st.plotly_chart(hierarchy_figure(cat), use_container_width=True)
        st.dataframe(asset_tree_table(cat), hide_index=True, use_container_width=True)
    if st.button("Continue to process signals", type="primary"):
        goto("signals")


def step_signals() -> None:
    cat = catalog()
    asset = st.session_state.selected_asset or (roots(cat)[0] if cat.assets else None)
    if asset is None:
        st.warning("Select equipment on the site graph first.")
        return
    header("Process signals", f"ProcessSignal instances linked to {asset['name']}")
    related = related_rows(cat, asset["external_id"])
    ts_list = related["timeseries"] or cat.timeseries[:4]
    if not ts_list:
        st.info("No ProcessSignal nodes on this equipment.")
        return
    selected = st.multiselect(
        "Signals",
        ts_list,
        default=ts_list[: min(3, len(ts_list))],
        format_func=lambda t: f"{t['name']} ({t.get('unit') or '—'})",
    )
    if not selected:
        return
    cdf = client()
    frames = []
    for ts in selected:
        frame = signal_frame(cdf, ts)
        if frame.empty:
            continue
        col = frame.columns[0]
        frames.append(frame.rename(columns={col: ts["name"]}))
    st.dataframe(
        pd.DataFrame(
            [{"external_id": t["external_id"], "tag": t.get("external_tag"), "unit": t.get("unit")} for t in selected]
        ),
        hide_index=True,
        use_container_width=True,
    )
    if frames:
        merged = pd.concat(frames, axis=1).sort_index()
        st.line_chart(merged)
        st.download_button(
            "Download selected signals (CSV)",
            timeseries_csv(merged),
            file_name="catalyst-context-signals.csv",
            mime="text/csv",
        )
    else:
        st.caption("No classic time-series datapoints for these ProcessSignal.externalTag values.")
    if st.session_state.industry in {"pharma", "both"} and cat.batches:
        st.markdown("**Batch instances**")
        st.dataframe(pd.DataFrame(cat.batches), hide_index=True, use_container_width=True)
    if st.button("Open canvas", type="primary"):
        goto("canvas")


def step_integrity() -> None:
    cat = catalog()
    asset = st.session_state.selected_asset
    profile = PROFILES[st.session_state.industry]
    header("Quality and integrity", profile.use_cases[1] if len(profile.use_cases) > 1 else profile.promise)
    events = cat.events
    files = cat.files
    if asset:
        related = related_rows(cat, asset["external_id"])
        events = related["events"] or events
        files = related["files"] or files
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**ProcessEvent**")
        if not events:
            st.caption("No ProcessEvent instances in this subtree.")
        for ev in events:
            kind = (ev.get("type") or "").lower()
            cls = "event"
            if kind in {"alarm", "deviation"}:
                cls += " warn"
            if (ev.get("subtype") or "").lower() in {"oos", "integrity"}:
                cls += " bad"
            st.markdown(
                f'<div class="{cls}"><b>{ev.get("subtype") or ev.get("type")}</b> · {ev.get("description")}'
                f'<div class="meta">{ev.get("type")} · {ev.get("asset_external_id")}</div></div>',
                unsafe_allow_html=True,
            )
    with c2:
        st.markdown("**EngineeringFile**")
        file_df = pd.DataFrame(files)
        if not file_df.empty:
            cols = [c for c in ("name", "mime_type", "asset_external_id") if c in file_df.columns]
            st.dataframe(file_df[cols], hide_index=True, use_container_width=True)
        else:
            st.caption("No EngineeringFile instances in this subtree.")
    if cat.quality:
        st.markdown("**QualityResult**")
        st.dataframe(pd.DataFrame(cat.quality), hide_index=True, use_container_width=True)
    if st.button("Build context pack", type="primary"):
        goto("context")


def step_context() -> None:
    cat = catalog()
    asset = st.session_state.selected_asset or (cat.assets[0] if cat.assets else None)
    if asset is None:
        st.warning("No equipment instance available.")
        return
    header("Context pack", "Export the selected twin from CatalystContext views.")
    pack = context_pack(cat, asset, st.session_state.industry)
    kpis(
        [
            ("Signals", len(pack["timeseries"])),
            ("Events", len(pack["events"])),
            ("Files", len(pack["files"])),
            ("Relationships", len(pack["relationships"])),
        ]
    )
    if HAS_PLOTLY:
        st.plotly_chart(context_network(pack), use_container_width=True)
    elif pack["relationships"]:
        st.dataframe(pd.DataFrame(pack["relationships"]), hide_index=True, use_container_width=True)
    with st.expander("Inspect JSON pack"):
        st.json(pack)
    st.download_button(
        "Download context pack (JSON)",
        pack_json(pack),
        file_name=f"catalyst-context-{asset['external_id']}.json",
        mime="application/json",
    )
    st.caption(f"Created by {CREATOR}")
    if st.button("Ask Atlas AI", type="primary"):
        goto("atlas")


def _merged_signals(cdf, selected: list[dict]) -> pd.DataFrame:
    frames = []
    for ts in selected:
        frame = signal_frame(cdf, ts)
        if frame.empty:
            continue
        col = frame.columns[0]
        frames.append(frame.rename(columns={col: ts["name"]}))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, axis=1).sort_index()


def step_canvas() -> None:
    cat = catalog()
    asset = st.session_state.selected_asset or (roots(cat)[0] if cat.assets else None)
    if asset is None:
        st.warning("Select equipment on the site graph first.")
        return
    header("Canvas", f"Time series and comparison charts for {asset['name']}")
    related = related_rows(cat, asset["external_id"])
    ts_list = related["timeseries"] or cat.timeseries[:6]
    selected = st.multiselect(
        "Signals on canvas",
        ts_list,
        default=ts_list[: min(3, len(ts_list))],
        format_func=lambda t: f"{t['name']} ({t.get('unit') or '—'})",
        key="canvas_signals",
    )
    cdf = client()
    merged = _merged_signals(cdf, selected) if selected else pd.DataFrame()
    left, right = st.columns(2)
    with left:
        st.markdown("**Time series**")
        if merged.empty:
            st.caption("No datapoints for the selected signals.")
        elif HAS_PLOTLY:
            fig = go.Figure()
            for col in merged.columns:
                fig.add_trace(go.Scatter(x=merged.index, y=merged[col], name=col, mode="lines"))
            st.plotly_chart(style_fig(fig, height=380), use_container_width=True)
        else:
            st.line_chart(merged)
    with right:
        st.markdown("**Latest values**")
        if merged.empty:
            st.caption("Select signals to compare latest readings.")
        else:
            latest = pd.DataFrame(
                [{"signal": col, "latest": float(merged[col].dropna().iloc[-1])} for col in merged.columns]
            )
            if HAS_PLOTLY:
                fig = px.bar(latest, x="signal", y="latest", color="signal", color_discrete_sequence=["#0f766e", "#d97706", "#0ea5e9", "#78716c"])
                fig.update_layout(showlegend=False)
                st.plotly_chart(style_fig(fig, height=380), use_container_width=True)
            else:
                st.bar_chart(latest.set_index("signal"))

    batches = related.get("batches") or (cat.batches if st.session_state.industry in {"pharma", "both"} else [])
    if batches:
        st.markdown("**Golden batch vs current / prior**")
        batch_df = pd.DataFrame(batches)
        show_cols = [c for c in ("batch_id", "recipe", "status", "yield_pct", "cycle_h", "deviations") if c in batch_df.columns]
        st.dataframe(batch_df[show_cols] if show_cols else batch_df, hide_index=True, use_container_width=True)
        metric_df = pd.DataFrame(
            [
                {
                    "batch": b.get("batch_id"),
                    "Yield %": b.get("yield_pct"),
                    "Cycle hours": b.get("cycle_h"),
                    "Deviations": b.get("deviations"),
                }
                for b in batches
            ]
        )
        c1, c2 = st.columns(2)
        with c1:
            long = metric_df.melt(id_vars="batch", var_name="metric", value_name="value")
            if HAS_PLOTLY:
                fig = px.bar(long, x="metric", y="value", color="batch", barmode="group", color_discrete_sequence=["#0f766e", "#d97706", "#0ea5e9"])
                st.plotly_chart(style_fig(fig, height=360), use_container_width=True)
            else:
                st.bar_chart(metric_df.set_index("batch"))
        with c2:
            st.markdown("**DO overlay (golden vs current)**")
            golden = synthetic_frame("HP-DS-23991", offset=8)
            current = synthetic_frame("HP-DS-24018", offset=-4)
            overlay = golden.rename(columns={golden.columns[0]: "Golden HP-DS-23991"}).join(
                current.rename(columns={current.columns[0]: "Current HP-DS-24018"}),
                how="outer",
            )
            if HAS_PLOTLY:
                fig = go.Figure()
                for col in overlay.columns:
                    fig.add_trace(go.Scatter(x=overlay.index, y=overlay[col], name=col, mode="lines"))
                st.plotly_chart(style_fig(fig, height=360), use_container_width=True)
            else:
                st.line_chart(overlay)
    if st.button("Continue to quality and integrity", type="primary"):
        goto("integrity")


def step_atlas() -> None:
    cat = catalog()
    header("Atlas AI", "Ask about equipment, batches, deviations, and files on CatalystContext.")
    if st.session_state.atlas_ready is None:
        ok, detail = ensure_atlas_agent(client())
        st.session_state.atlas_ready = ok
        st.session_state.atlas_error = detail if not ok else ""
    if st.session_state.atlas_ready:
        st.caption(f"{ATLAS_AGENT_NAME} · `{ATLAS_AGENT_ID}`")
    else:
        st.warning(
            "Atlas agent upsert/chat is not enabled on this project "
            f"({st.session_state.get('atlas_error', '')}). Answers use loaded instances."
        )
    for msg in st.session_state.atlas_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    prompt = st.chat_input("Ask Atlas about BRX-04, golden batch, files, or deviations")
    if prompt:
        st.session_state.atlas_messages.append({"role": "user", "content": prompt})
        reply = None
        if st.session_state.atlas_ready:
            try:
                reply, cursor = atlas_chat(client(), prompt, st.session_state.atlas_cursor)
                st.session_state.atlas_cursor = cursor
            except Exception as exc:
                st.session_state.atlas_ready = False
                st.session_state.atlas_error = f"{type(exc).__name__}: {exc}"
                reply = catalog_fallback(cat, prompt)
        else:
            reply = catalog_fallback(cat, prompt)
        st.session_state.atlas_messages.append({"role": "assistant", "content": reply})
        st.rerun()
    cols = st.columns(3)
    if cols[0].button("Golden vs current batch"):
        st.session_state["_atlas_preset"] = "Compare golden batch HP-DS-23991 with current HP-DS-24018. What differs?"
    if cols[1].button("Files on BRX-04"):
        st.session_state["_atlas_preset"] = "Which engineering files are linked to bioreactor BRX-04?"
    if cols[2].button("DO deviation"):
        st.session_state["_atlas_preset"] = "What process deviation happened on BRX-04 and which tags matter?"
    preset = st.session_state.pop("_atlas_preset", None)
    if preset:
        st.session_state.atlas_messages.append({"role": "user", "content": preset})
        if st.session_state.atlas_ready:
            try:
                reply, cursor = atlas_chat(client(), preset, st.session_state.atlas_cursor)
                st.session_state.atlas_cursor = cursor
            except Exception as exc:
                st.session_state.atlas_ready = False
                st.session_state.atlas_error = f"{type(exc).__name__}: {exc}"
                reply = catalog_fallback(cat, preset)
        else:
            reply = catalog_fallback(cat, preset)
        st.session_state.atlas_messages.append({"role": "assistant", "content": reply})
        st.rerun()


def run() -> None:
    init_state()
    sidebar()
    try:
        {
            "lens": step_lens,
            "model": step_model,
            "site": step_site,
            "signals": step_signals,
            "canvas": step_canvas,
            "integrity": step_integrity,
            "context": step_context,
            "atlas": step_atlas,
        }[st.session_state.step]()
    except Exception as exc:
        st.error(f"Could not load CatalystContext data: {type(exc).__name__}: {exc}")
        st.caption(f"Created by {CREATOR}")


if __name__ == "__main__":
    run()
