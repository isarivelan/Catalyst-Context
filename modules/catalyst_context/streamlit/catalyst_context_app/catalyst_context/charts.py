"""SVG charts that render in Fusion Streamlit (Pyodide) without Plotly/Altair."""

from __future__ import annotations

import math
import sys

COLORS = ("#0f766e", "#d97706", "#0ea5e9", "#b91c1c", "#78716c", "#115e59")


def in_fusion_runtime() -> bool:
    return sys.platform == "emscripten" or "pyodide" in sys.modules


def _xml(text: object) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _numeric_frame(frame):
    import pandas as pd

    df = frame.copy()
    if len(df) > 90:
        df = df.iloc[:: max(1, len(df) // 90)]
    return df.select_dtypes(include="number") if not df.empty else pd.DataFrame()


def svg_line_chart(frame, height: int = 340, width: int = 720) -> str:
    ys = _numeric_frame(frame)
    if ys.empty:
        return ""
    ymin = float(ys.min().min())
    ymax = float(ys.max().max())
    if ymin == ymax:
        ymax = ymin + 1.0
    left, top, bottom = 48, 16, 36
    plot_w, plot_h = width - left - 16, height - top - bottom
    n = len(ys)

    def x_at(i: int) -> float:
        return left + plot_w * (i / max(n - 1, 1))

    def y_at(v: float) -> float:
        return top + plot_h * (1 - (v - ymin) / (ymax - ymin))

    parts = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" xmlns="http://www.w3.org/2000/svg" '
        'style="background:#fffcf7;border:1px solid #e7e5e4;border-radius:12px;margin:0.4rem 0;">',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#e7e5e4"/>',
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#e7e5e4"/>',
        f'<text x="6" y="{top + 8}" font-size="10" fill="#78716c">{ymax:.1f}</text>',
        f'<text x="6" y="{top + plot_h}" font-size="10" fill="#78716c">{ymin:.1f}</text>',
    ]
    legend = []
    for ci, col in enumerate(ys.columns):
        color = COLORS[ci % len(COLORS)]
        pts = []
        vals = ys[col].tolist()
        for i, v in enumerate(vals):
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if fv != fv:
                continue
            pts.append(f"{x_at(i):.1f},{y_at(fv):.1f}")
        if pts:
            parts.append(
                f'<polyline fill="none" stroke="{color}" stroke-width="2.2" points="{" ".join(pts)}"/>'
            )
            legend.append(
                f'<rect x="{left + ci * 130}" y="{height - 22}" width="10" height="10" rx="2" fill="{color}"/>'
                f'<text x="{left + 16 + ci * 130}" y="{height - 13}" font-size="11" fill="#44403c">{_xml(col)}</text>'
            )
    parts.extend(legend)
    parts.append("</svg>")
    return "".join(parts)


def svg_bar_chart(labels: list[str], values: list[float], height: int = 320, width: int = 720) -> str:
    if not labels:
        return ""
    nums = [float(v) if v is not None else 0.0 for v in values]
    vmax = max(nums) if nums else 1.0
    if vmax <= 0:
        vmax = 1.0
    left, top, bottom = 24, 16, 48
    plot_w, plot_h = width - left - 16, height - top - bottom
    bar_w = plot_w / max(len(labels), 1) * 0.62
    gap = plot_w / max(len(labels), 1)
    parts = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" xmlns="http://www.w3.org/2000/svg" '
        'style="background:#fffcf7;border:1px solid #e7e5e4;border-radius:12px;margin:0.4rem 0;">'
    ]
    for i, (label, val) in enumerate(zip(labels, nums)):
        bh = plot_h * (val / vmax)
        x = left + i * gap + (gap - bar_w) / 2
        y = top + plot_h - bh
        color = COLORS[i % len(COLORS)]
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{max(bh, 1):.1f}" rx="4" fill="{color}"/>'
        )
        parts.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{height - 16}" font-size="10" text-anchor="middle" fill="#44403c">{_xml(label)}</text>'
        )
        parts.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{y - 4:.1f}" font-size="10" text-anchor="middle" fill="#57534e">{val:.1f}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


def svg_grouped_bar(categories: list[str], series: dict[str, list[float]], height: int = 320, width: int = 720) -> str:
    if not categories or not series:
        return ""
    names = list(series.keys())
    left, top, bottom = 36, 16, 52
    plot_w, plot_h = width - left - 16, height - top - bottom
    group_w = plot_w / max(len(categories), 1)
    bar_w = group_w * 0.72 / max(len(names), 1)
    vmax = 1.0
    for vals in series.values():
        for v in vals:
            if v is not None and float(v) > vmax:
                vmax = float(v)
    parts = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" xmlns="http://www.w3.org/2000/svg" '
        'style="background:#fffcf7;border:1px solid #e7e5e4;border-radius:12px;margin:0.4rem 0;">'
    ]
    for i, cat in enumerate(categories):
        gx = left + i * group_w
        for j, name in enumerate(names):
            vals = series[name]
            val = float(vals[i]) if i < len(vals) and vals[i] is not None else 0.0
            bh = plot_h * (val / vmax)
            x = gx + group_w * 0.14 + j * bar_w
            y = top + plot_h - bh
            color = COLORS[j % len(COLORS)]
            parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w - 3:.1f}" height="{max(bh, 1):.1f}" rx="3" fill="{color}"/>'
            )
        parts.append(
            f'<text x="{gx + group_w / 2:.1f}" y="{height - 28}" font-size="11" text-anchor="middle" fill="#44403c">{_xml(cat)}</text>'
        )
    for j, name in enumerate(names):
        parts.append(
            f'<rect x="{left + j * 140}" y="{height - 16}" width="10" height="10" rx="2" fill="{COLORS[j % len(COLORS)]}"/>'
            f'<text x="{left + 16 + j * 140}" y="{height - 7}" font-size="11" fill="#44403c">{_xml(name)}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


def svg_network(pack: dict, height: int = 420, width: int = 720) -> str:
    nodes = [("asset", pack.get("asset", {}).get("name") or "Asset")]
    nodes += [("ts", t.get("name") or "") for t in pack.get("timeseries", [])[:6]]
    nodes += [("event", e.get("subtype") or e.get("type") or "event") for e in pack.get("events", [])[:6]]
    nodes += [("file", (f.get("name") or "")[:28]) for f in pack.get("files", [])[:6]]
    palette = {"asset": "#0f766e", "ts": "#0ea5e9", "event": "#d97706", "file": "#78716c"}
    cx, cy, radius = width / 2, height / 2 - 8, min(width, height) * 0.32
    n = max(len(nodes) - 1, 1)
    coords = [(cx, cy)]
    for i in range(1, len(nodes)):
        angle = 2 * math.pi * (i - 1) / n
        coords.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    parts = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" xmlns="http://www.w3.org/2000/svg" '
        'style="background:#fffcf7;border:1px solid #e7e5e4;border-radius:12px;margin:0.4rem 0;">'
    ]
    for i in range(1, len(coords)):
        x, y = coords[i]
        parts.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{x:.1f}" y2="{y:.1f}" stroke="#d6d3d1" stroke-width="1.6"/>')
    for (kind, label), (x, y) in zip(nodes, coords):
        r = 16 if kind == "asset" else 10
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{palette.get(kind, "#a8a29e")}"/>')
        parts.append(
            f'<text x="{x:.1f}" y="{y - r - 6:.1f}" font-size="11" text-anchor="middle" fill="#1c1917">{_xml(label)}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)
