"""Catalyst Context — custom Streamlit flow for a Cognite Data Fusion POC."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from catalyst_context.cdf_build import DATA_MODEL, TRANSFORMATION_JOBS, artifacts_present
from catalyst_context.cdf_client import connect
from catalyst_context.profiles import FLOW_STEPS, PROFILES
from catalyst_context.services import (
    children,
    context_pack,
    load_catalog,
    pack_json,
    related_rows,
    roots,
    settings,
    signal_frame,
    timeseries_csv,
)

st.set_page_config(
    page_title="Catalyst Context",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

STEP_KEYS = [k for k, _ in FLOW_STEPS]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,560;9..144,680&family=Source+Sans+3:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Source Sans 3', sans-serif; }
[data-testid="stHeader"] { background: transparent; height: 0; }
[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"],
.stDeployButton, #MainMenu, footer { display: none !important; }
[data-testid="stSidebar"] { background: #1c1917; }
[data-testid="stSidebar"] * { color: #f5f5f4 !important; }
[data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: #a8a29e !important; }
.block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1180px; }
.brand-mark { font-size: 0.72rem; letter-spacing: 0.22em; text-transform: uppercase; color: #d6d3d1; font-weight: 600; }
.brand-title { font-family: Fraunces, Georgia, serif; font-size: 1.35rem; margin: 0.2rem 0 0.15rem 0; color: #fffbeb; }
.hero-kicker { letter-spacing: 0.18em; text-transform: uppercase; color: #0f766e; font-size: 0.75rem; font-weight: 700; }
.hero-title { font-family: Fraunces, Georgia, serif; font-size: 2.15rem; font-weight: 680; margin: 0.2rem 0 0.4rem 0; line-height: 1.15; color: #1c1917; }
.hero-sub { color: #57534e; font-size: 1.05rem; margin-bottom: 1.2rem; max-width: 46rem; }
.step-rail { background: #0c0a09; border: 1px solid #44403c; border-radius: 16px; padding: 0.75rem; margin: 0.8rem 0 1rem 0; }
.step-item { padding: 0.5rem 0.65rem; border-radius: 10px; margin-bottom: 0.28rem; font-size: 0.88rem; color: #a8a29e; }
.step-item.active { background: #0f766e; color: #ecfdf5; font-weight: 700; }
.step-item.done { color: #5eead4; }
.kpi { background: #fffcf7; border: 1px solid #e7e5e4; border-radius: 14px; padding: 0.9rem 1rem; }
.kpi .label { color: #78716c; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; }
.kpi .value { font-family: Fraunces, Georgia, serif; font-size: 1.55rem; font-weight: 680; color: #1c1917; }
.card { border: 1px solid #e7e5e4; border-radius: 16px; padding: 1.1rem 1.15rem; background: #fffcf7; min-height: 9.2rem; }
.card h4 { font-family: Fraunces, Georgia, serif; margin: 0 0 0.4rem 0; font-size: 1.2rem; }
.card p { color: #57534e; margin: 0; line-height: 1.45; }
.chip { display: inline-block; background: #ecfdf5; color: #115e59; border-radius: 999px; padding: 0.15rem 0.6rem; font-size: 0.75rem; font-weight: 600; margin-bottom: 0.55rem; }
.event { border-left: 4px solid #0f766e; background: #fffcf7; border-radius: 0 12px 12px 0; padding: 0.7rem 0.9rem; margin-bottom: 0.55rem; border: 1px solid #e7e5e4; }
.event.warn { border-left-color: #d97706; }
.event.bad { border-left-color: #b91c1c; }
.event .meta { color: #78716c; font-size: 0.78rem; }
.pipe { display: flex; gap: 0.5rem; flex-wrap: wrap; margin: 0.6rem 0 1.1rem 0; }
.pipe span { background: #1c1917; color: #fffbeb; border-radius: 999px; padding: 0.35rem 0.8rem; font-size: 0.82rem; }
.pipe em { background: transparent; color: #78716c; font-style: normal; padding: 0.35rem 0.1rem; }
.note { color: #78716c; font-size: 0.9rem; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def init_state() -> None:
    st.session_state.setdefault("step", "lens")
    st.session_state.setdefault("industry", "both")
    st.session_state.setdefault("mode", "demo")
    st.session_state.setdefault("client", None)
    st.session_state.setdefault("connect_error", "")
    st.session_state.setdefault("selected_asset", None)
    st.session_state.setdefault("selected_ts", None)


def goto(step: str) -> None:
    st.session_state.step = step
    st.rerun()


def catalog():
    return load_catalog(
        st.session_state.mode,
        st.session_state.industry,
        live_client=st.session_state.client,
    )


def kpis(items: list[tuple[str, str | int]]) -> None:
    cols = st.columns(len(items))
    for col, (label, value) in zip(cols, items):
        col.markdown(
            f'<div class="kpi"><div class="label">{label}</div><div class="value">{value}</div></div>',
            unsafe_allow_html=True,
        )


def style_fig(fig: go.Figure, height: int = 400) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(t=28, l=10, r=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#fffcf7",
        font=dict(family="Source Sans 3, sans-serif", color="#1c1917", size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, title=""),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#e7e5e4", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#e7e5e4", zeroline=False)
    return fig


def sidebar() -> None:
    with st.sidebar:
        st.markdown('<div class="brand-mark">Process industries · CDF POC</div>', unsafe_allow_html=True)
        st.markdown('<div class="brand-title">Catalyst Context</div>', unsafe_allow_html=True)
        current = st.session_state.step
        current_idx = STEP_KEYS.index(current)
        html = ['<div class="step-rail">']
        for i, (key, label) in enumerate(FLOW_STEPS):
            cls = "step-item"
            if key == current:
                cls += " active"
            elif i < current_idx:
                cls += " done"
            html.append(f'<div class="{cls}">{i + 1:02d}  {label}</div>')
        html.append("</div>")
        st.markdown("\n".join(html), unsafe_allow_html=True)
        profile = PROFILES[st.session_state.industry]
        st.caption("Industry lens")
        st.write(profile.title)
        st.caption("Catalog")
        st.write("Live CDF" if st.session_state.mode == "live" else "Guided demo · synthetic")
        cols = st.columns(2)
        idx = STEP_KEYS.index(st.session_state.step)
        if idx > 0 and cols[0].button("Back", use_container_width=True):
            goto(STEP_KEYS[idx - 1])
        if idx < len(STEP_KEYS) - 1 and cols[1].button("Next", use_container_width=True, type="primary"):
            goto(STEP_KEYS[idx + 1])


def header(title: str, subtitle: str) -> None:
    st.markdown('<div class="hero-kicker">Catalyst Context</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="hero-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="hero-sub">{subtitle}</div>', unsafe_allow_html=True)


def step_lens() -> None:
    header(
        "One contextualization flow for process industries",
        "A stakeholder POC that speaks batch manufacturing and energy operations — without changing the CDF pattern.",
    )
    cols = st.columns(3)
    cards = [
        ("pharma", "Life sciences", "ISA-88/95 batch, LIMS, golden batch, deviations."),
        ("oil_gas", "Oil and gas", "Rotating equipment, P&IDs, PI historian, allocation."),
        ("both", "Shared pattern", "Asset → signal → event → file. Reuse across sites."),
    ]
    for col, (key, title, body) in zip(cols, cards):
        selected = st.session_state.industry == key
        chip = "Selected" if selected else "Choose lens"
        with col:
            st.markdown(
                f'<div class="card"><div class="chip">{chip}</div><h4>{title}</h4><p>{body}</p></div>',
                unsafe_allow_html=True,
            )
            if st.button(f"Use {title}", key=f"pick_{key}", use_container_width=True, type="primary" if selected else "secondary"):
                st.session_state.industry = key
                goto("connect")

    profile = PROFILES[st.session_state.industry]
    kpis(
        [
            ("Demo assets", "17"),
            ("Time series", "14"),
            ("Datapoints", "2,352"),
            ("Events / files", "8 / 8"),
        ]
    )
    st.markdown("")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Typical sources**")
        for src in profile.sources:
            st.write(f"- {src}")
    with c2:
        st.markdown("**What this POC proves**")
        st.write(profile.promise)
        for use in profile.use_cases[:2]:
            st.write(f"- {use}")


def step_connect() -> None:
    header(
        "Connect the industrial graph",
        "Demo catalog is already loaded. Space, containers, views, and the data model live in `modules/catalyst_context` — they are not published until you deploy.",
    )
    deployed = artifacts_present()
    st.markdown(
        '<div class="pipe">'
        "<span>RAW CSV</span><em>→</em>"
        "<span>4 transformation jobs</span><em>→</em>"
        "<span>CatalystContext v1 · 7 containers · 7 views</span><em>→</em>"
        "<span>Streamlit flow</span>"
        "</div>",
        unsafe_allow_html=True,
    )
    kpis(
        [
            ("Space", DATA_MODEL["space"]),
            ("Data model", f"{DATA_MODEL['external_id']} {DATA_MODEL['version']}"),
            ("Containers / views", f"{len(DATA_MODEL['containers'])} / {len(DATA_MODEL['views'])}"),
            ("Transform jobs", len(TRANSFORMATION_JOBS)),
        ]
    )
    st.caption(DATA_MODEL["status"] + (f" · files on disk: {'yes' if deployed else 'missing'}" ))

    left, right = st.columns((1.05, 1))
    with left:
        st.markdown("**Containers and views**")
        st.dataframe(
            pd.DataFrame(DATA_MODEL["views"]),
            hide_index=True,
            use_container_width=True,
        )
    with right:
        st.markdown("**Transformation jobs**")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "job": job["external_id"],
                        "from": job["source"],
                        "to": job["destination"],
                    }
                    for job in TRANSFORMATION_JOBS
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )

    st.markdown("")
    mode = st.radio(
        "Catalog source",
        options=["demo", "live"],
        format_func=lambda m: "Guided demo (synthetic graph, no CDF login)" if m == "demo" else "Live CDF (OIDC client credentials)",
        index=0 if st.session_state.mode == "demo" else 1,
        horizontal=True,
    )
    st.session_state.mode = mode

    if mode == "demo":
        st.info("Helix Park Biologics + Harbor Ridge compression train. 17 assets, 14 tags × 168 hourly points, 8 events, 8 files, 3 batches.")
        if st.button("Open site graph", type="primary"):
            st.session_state.client = None
            goto("site")
        return

    cfg = settings()
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="kpi"><div class="label">Project</div><div class="value">{cfg.project or "—"}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi"><div class="label">Cluster</div><div class="value">{cfg.cluster or "—"}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi"><div class="label">Tenant</div><div class="value">{(cfg.tenant_id[:8] + "…") if cfg.tenant_id else "—"}</div></div>', unsafe_allow_html=True)
    if not cfg.ready:
        st.warning(
            "Copy `.env.example` to `.env` and set CDF_PROJECT, CDF_CLUSTER, "
            "IDP_TENANT_ID, IDP_CLIENT_ID, IDP_CLIENT_SECRET."
        )
        return
    if st.button("Inspect token and load catalog", type="primary"):
        try:
            client = connect(cfg)
            inspect = client.iam.token.inspect()
            st.session_state.client = client
            st.session_state.connect_error = ""
            st.success(f"Connected to `{cfg.project}` as `catalyst-context-poc`.")
            st.json({"projects": getattr(inspect, "projects", None) or str(inspect)[:800]})
        except Exception as exc:
            st.session_state.client = None
            st.error(f"Connection failed: {exc}")
    if st.session_state.client and st.button("Open site graph"):
        goto("site")


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
    header("Site graph", f"{profile.hierarchy[0]} → {profile.hierarchy[-1]}  ·  {cat.project}")
    kpis(
        [
            ("Assets", len(cat.assets)),
            ("Time series", len(cat.timeseries)),
            ("Events", len(cat.events)),
            ("Files", len(cat.files)),
        ]
    )
    st.markdown("")
    left, right = st.columns((1, 1.4))
    with left:
        root_opts = roots(cat)
        if not root_opts:
            st.info("No assets returned. Check CDF ACL or stay in demo mode.")
            return
        root = st.selectbox("Root site / field", root_opts, format_func=lambda a: a["name"])
        level2 = children(cat, root["external_id"]) or [root]
        area = st.selectbox("Area / system", level2, format_func=lambda a: a["name"])
        level3 = children(cat, area["external_id"]) or [area]
        unit = st.selectbox("Unit / equipment", level3, format_func=lambda a: a["name"])
        st.session_state.selected_asset = unit
        st.markdown(f"**{unit['name']}**")
        st.caption(unit.get("description") or "")
        meta = unit.get("metadata") or {}
        if meta:
            st.dataframe(pd.DataFrame([meta]), hide_index=True, use_container_width=True)
    with right:
        fig = hierarchy_figure(cat)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(asset_tree_table(cat), hide_index=True, use_container_width=True)
    if st.button("Continue to process signals", type="primary"):
        goto("signals")


def hierarchy_figure(cat) -> go.Figure:
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


def step_signals() -> None:
    cat = catalog()
    asset = st.session_state.selected_asset or (roots(cat)[0] if cat.assets else None)
    if asset is None:
        st.warning("Select an asset on the site graph step first.")
        return
    header("Process signals", f"Historian-style trends contextualized to {asset['name']}")
    related = related_rows(cat, asset["external_id"])
    ts_list = related["timeseries"] or cat.timeseries[:4]
    if not ts_list:
        st.info("No time series on this asset.")
        return
    selected = st.multiselect(
        "Signals",
        ts_list,
        default=ts_list[: min(3, len(ts_list))],
        format_func=lambda t: f"{t['name']} ({t.get('unit') or '—'})",
    )
    if not selected:
        return
    st.session_state.selected_ts = selected[0]
    frames = []
    for ts in selected:
        frame = signal_frame(st.session_state.mode, ts, st.session_state.client)
        if frame.empty:
            continue
        col = frame.columns[0]
        frames.append(frame.rename(columns={col: ts["name"]}))
    if not frames:
        st.info("No datapoints returned.")
        return
    merged = pd.concat(frames, axis=1).sort_index()
    fig = px.line(merged, color_discrete_sequence=["#0f766e", "#d97706", "#44403c", "#0ea5e9"])
    fig.update_layout(xaxis_title="Time (UTC)", yaxis_title="Value")
    st.plotly_chart(style_fig(fig, height=440), use_container_width=True)
    st.caption(f"{len(merged):,} hourly samples per selected tag in the demo window (7 days).")
    st.download_button(
        "Download selected signals (CSV)",
        timeseries_csv(merged),
        file_name="catalyst-context-signals.csv",
        mime="text/csv",
    )
    if st.session_state.industry in {"pharma", "both"} and cat.batches:
        st.markdown("**Golden batch vs current**")
        st.dataframe(pd.DataFrame(cat.batches), hide_index=True, use_container_width=True)
    if st.button("Continue to quality and integrity", type="primary"):
        goto("integrity")


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
        st.markdown("**Events · deviations · work orders**")
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
        st.markdown("**Files · P&IDs · batch records · CoA**")
        file_df = pd.DataFrame(files)
        if not file_df.empty:
            show = file_df[["name", "mime_type", "asset_external_id"]].rename(
                columns={"mime_type": "type", "asset_external_id": "linked asset"}
            )
            st.dataframe(show, hide_index=True, use_container_width=True)
        else:
            st.caption("No files on this subtree.")
    st.markdown(
        '<p class="note">These rows are what transformation jobs would write into ProcessEvent and EngineeringFile views.</p>',
        unsafe_allow_html=True,
    )
    if st.button("Build context pack", type="primary"):
        goto("context")


def step_context() -> None:
    cat = catalog()
    asset = st.session_state.selected_asset or (cat.assets[0] if cat.assets else None)
    if asset is None:
        st.warning("No asset available.")
        return
    header("Context pack", "Export the selected twin: equipment + signals + events + files + relationships.")
    pack = context_pack(cat, asset, st.session_state.industry)
    kpis(
        [
            ("Signals", len(pack["timeseries"])),
            ("Events", len(pack["events"])),
            ("Files", len(pack["files"])),
            ("Relationships", len(pack["relationships"])),
        ]
    )
    st.plotly_chart(style_fig(context_network(pack), height=430), use_container_width=True)
    with st.expander("Inspect JSON pack"):
        st.json(pack)
    st.download_button(
        "Download context pack (JSON)",
        pack_json(pack),
        file_name=f"catalyst-context-{asset['external_id']}.json",
        mime="application/json",
    )
    st.markdown("**Why this matters**")
    for use in PROFILES[st.session_state.industry].use_cases:
        st.write(f"- {use}")


def context_network(pack: dict) -> go.Figure:
    import math

    nodes = [("asset", pack["asset"]["name"])]
    nodes += [("ts", t["name"]) for t in pack["timeseries"][:6]]
    nodes += [("event", e["subtype"] or e["type"]) for e in pack["events"][:6]]
    nodes += [("file", f["name"][:28]) for f in pack["files"][:6]]
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
    return fig


def main() -> None:
    init_state()
    sidebar()
    {
        "lens": step_lens,
        "connect": step_connect,
        "site": step_site,
        "signals": step_signals,
        "integrity": step_integrity,
        "context": step_context,
    }[st.session_state.step]()


main()
