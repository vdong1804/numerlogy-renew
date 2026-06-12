"""Pure SVG chart generators for the numerology PDF report (no I/O, no DB).

Produces 4 inline-SVG strings from the `calc` dict (calculate_numerology_numbers):
  power_bar      — digit-frequency bars (1..9)
  core_radar     — 6-axis radar of the core numbers
  peaks_timeline — 4 life-peak milestones along an age axis
  cycle_wheel    — 9-year personal-year donut, current year highlighted

Palette/geometry primitives live in report_charts_geometry.py. Colours are tuned
to read on the dark "cosmic" chart page (gold on navy); CSS classes
(.chart-bar/.chart-radar/…) control display size. Hand-built SVG — no matplotlib,
no unicode astro glyphs.
"""

from __future__ import annotations

from app.services.report_charts_geometry import (
    CREAM, FILL, GOLD, GOLD_SOFT, GRID, NAVY, RADAR_AXES, cap9, n, pt,
)


# ── 1. Power bars ────────────────────────────────────────────────────────────
def power_bar_svg(counts: dict[str, int]) -> str:
    """Frequency bars for digits 1..9. `counts` = {"1": n, …}."""
    maxv = max([*counts.values(), 1]) or 1
    base, top, slot = 165.0, 20.0, 320.0 / 9
    bars = []
    for d in range(1, 10):
        v = int(counts.get(str(d), 0))
        h = (v / maxv) * (base - top)
        x = 20 + (d - 1) * slot + slot * 0.18
        bw = slot * 0.64
        by = base - h
        bars.append(
            f'<rect x="{n(x)}" y="{n(by)}" width="{n(bw)}" height="{n(h)}" '
            f'rx="2" fill="{GOLD}"/>'
        )
        if v:
            bars.append(
                f'<text x="{n(x + bw / 2)}" y="{n(by - 4)}" text-anchor="middle" '
                f'font-size="11" fill="{GOLD_SOFT}">{v}</text>'
            )
        bars.append(
            f'<text x="{n(x + bw / 2)}" y="184" text-anchor="middle" '
            f'font-size="13" font-weight="700" fill="{CREAM}">{d}</text>'
        )
    return (
        '<svg class="chart-svg chart-bar" viewBox="0 0 360 200" '
        'xmlns="http://www.w3.org/2000/svg">'
        f'<line x1="16" y1="{n(base)}" x2="344" y2="{n(base)}" '
        f'stroke="{GRID}" stroke-width="1"/>'
        + "".join(bars)
        + "</svg>"
    )


# ── 2. Core radar ────────────────────────────────────────────────────────────
def core_radar_svg(values: dict[str, int]) -> str:
    """Radar over the core numbers. `values` = {"so_chu_dao": n, …}."""
    # Wider viewBox (420) so the longest side labels ("Trưởng thành") never
    # clip past the left/right edges.
    cx, cy, R = 210.0, 175.0, 120.0
    axes = [(lbl, key) for lbl, key in RADAR_AXES if key in values]
    count = len(axes)
    if count < 3:
        return ""
    step = 360.0 / count
    parts = []
    for frac in (0.34, 0.67, 1.0):  # concentric grid rings
        ring = " ".join(
            n(c) for i in range(count) for c in pt(cx, cy, R * frac, i * step)
        )
        parts.append(f'<polygon points="{ring}" fill="none" stroke="{GRID}"/>')
    data, labels = [], []
    for i, (lbl, key) in enumerate(axes):
        deg = i * step
        ox, oy = pt(cx, cy, R, deg)
        parts.append(
            f'<line x1="{n(cx)}" y1="{n(cy)}" x2="{n(ox)}" y2="{n(oy)}" stroke="{GRID}"/>'
        )
        dx, dy = pt(cx, cy, R * (cap9(values[key]) / 9), deg)
        data.append((dx, dy))
        lx, ly = pt(cx, cy, R + 22, deg)
        anchor = "middle" if abs(lx - cx) < 8 else ("start" if lx > cx else "end")
        labels.append(
            f'<text x="{n(lx)}" y="{n(ly)}" text-anchor="{anchor}" '
            f'font-size="11" fill="{CREAM}">{lbl} '
            f'<tspan fill="{GOLD_SOFT}" font-weight="700">{values[key]}</tspan></text>'
        )
    poly = " ".join(f"{n(x)},{n(y)}" for x, y in data)
    parts.append(
        f'<polygon points="{poly}" fill="{FILL}" stroke="{GOLD}" stroke-width="2"/>'
    )
    for px, py in data:
        parts.append(f'<circle cx="{n(px)}" cy="{n(py)}" r="3" fill="{GOLD_SOFT}"/>')
    return (
        '<svg class="chart-svg chart-radar" viewBox="0 0 420 350" '
        'xmlns="http://www.w3.org/2000/svg">' + "".join(parts) + "".join(labels) + "</svg>"
    )


# ── 3. Peaks timeline ────────────────────────────────────────────────────────
def peaks_timeline_svg(peaks: list[dict]) -> str:
    """4 life-peak nodes along an age axis. peak number in node, challenge above."""
    items = sorted(peaks, key=lambda p: p.get("age_start", 0))
    if not items:
        return ""
    y, x0, x1 = 95.0, 34.0, 326.0
    gap = (x1 - x0) / max(len(items) - 1, 1)
    parts = [f'<line x1="{n(x0)}" y1="{n(y)}" x2="{n(x1)}" y2="{n(y)}" '
             f'stroke="{GRID}" stroke-width="2"/>']
    for i, p in enumerate(items):
        x = x0 + i * gap
        parts += [
            f'<text x="{n(x)}" y="40" text-anchor="middle" font-size="10" '
            f'fill="{GOLD_SOFT}">Thử thách {p.get("challenge", "")}</text>',
            f'<circle cx="{n(x)}" cy="{n(y)}" r="22" fill="{NAVY}" '
            f'stroke="{GOLD}" stroke-width="2"/>',
            f'<text x="{n(x)}" y="{n(y + 7)}" text-anchor="middle" font-size="20" '
            f'font-weight="700" fill="{GOLD_SOFT}">{p.get("peak", "")}</text>',
            f'<text x="{n(x)}" y="150" text-anchor="middle" font-size="11" '
            f'fill="{CREAM}">Đỉnh {p.get("stage", i + 1)}</text>',
            f'<text x="{n(x)}" y="166" text-anchor="middle" font-size="10" '
            f'fill="{GOLD_SOFT}">~ tuổi {p.get("age_start", "")}</text>',
        ]
    return (
        '<svg class="chart-svg chart-timeline" viewBox="0 0 360 180" '
        'xmlns="http://www.w3.org/2000/svg">' + "".join(parts) + "</svg>"
    )


# ── 4. Cycle wheel ───────────────────────────────────────────────────────────
def cycle_wheel_svg(personal_year: int) -> str:
    """9-year donut; the current personal-year segment is highlighted."""
    cy_now = cap9(personal_year) or 9
    cx, cy, ro, ri = 160.0, 160.0, 130.0, 72.0
    seg = 40.0
    parts = []
    for i in range(9):
        year = i + 1
        a0, a1 = i * seg, (i + 1) * seg
        active = year == cy_now
        p0o, p1o = pt(cx, cy, ro, a0), pt(cx, cy, ro, a1)
        p1i, p0i = pt(cx, cy, ri, a1), pt(cx, cy, ri, a0)
        path = (
            f"M{n(p0o[0])},{n(p0o[1])} A{ro} {ro} 0 0 1 {n(p1o[0])},{n(p1o[1])} "
            f"L{n(p1i[0])},{n(p1i[1])} A{ri} {ri} 0 0 0 {n(p0i[0])},{n(p0i[1])} Z"
        )
        fill = GOLD if active else "rgba(201,162,39,.10)"
        parts.append(f'<path d="{path}" fill="{fill}" stroke="{GRID}"/>')
        tx, ty = pt(cx, cy, (ro + ri) / 2, a0 + seg / 2)
        parts.append(
            f'<text x="{n(tx)}" y="{n(ty + 5)}" text-anchor="middle" font-size="15" '
            f'font-weight="700" fill="{NAVY if active else CREAM}">{year}</text>'
        )
    return (
        '<svg class="chart-svg chart-wheel" viewBox="0 0 320 320" '
        'xmlns="http://www.w3.org/2000/svg">' + "".join(parts) + "</svg>"
    )


# ── Orchestration ────────────────────────────────────────────────────────────
def build_charts(calc: dict, birth_day: str = "") -> dict[str, str | None]:
    """Build the 4 chart SVGs from a calc dict. Missing keys → None for that chart."""
    out: dict[str, str | None] = {"power": None, "radar": None, "timeline": None, "wheel": None}
    try:
        text_name = calc.get("text_name", "")
        counts = {
            str(d): birth_day.count(str(d)) + text_name.count(str(d))
            for d in range(1, 10)
        }
        out["power"] = power_bar_svg(counts)
    except Exception:  # noqa: BLE001 — fail-safe, never break a report
        pass
    try:
        values = {key: calc[key] for _, key in RADAR_AXES if key in calc}
        out["radar"] = core_radar_svg(values) or None
    except Exception:  # noqa: BLE001
        pass
    try:
        peaks = [
            {
                "stage": i,
                "age_start": calc[f"tuoi_dinh_cao_{i}"],
                "peak": calc[f"dinh_cao_{i}"],
                "challenge": calc[f"thu_thach_{i}"],
            }
            for i in range(1, 5)
        ]
        out["timeline"] = peaks_timeline_svg(peaks) or None
    except Exception:  # noqa: BLE001
        pass
    try:
        out["wheel"] = cycle_wheel_svg(calc["so_nam_ca_nhan"])
    except Exception:  # noqa: BLE001
        pass
    return out
