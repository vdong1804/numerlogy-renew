"""Shared palette + geometry primitives for report_charts.py (pure, no I/O).

Split out so report_charts.py (the 4 chart generators + orchestration) stays
under the 200-line module budget. Palette mirrors reports/_theme.css.
"""

from __future__ import annotations

import math

# ── Palette (sync with _theme.css) ──────────────────────────────────────────
NAVY = "#002060"
GOLD = "#c9a227"
GOLD_SOFT = "#e3c970"
VERMILION = "#b0392b"
CREAM = "#fbf8f0"
GRID = "rgba(201,162,39,.30)"          # faint gold gridlines
FILL = "rgba(201,162,39,.22)"          # translucent gold polygon fill

# Core radar axes: short label → calc key (order = clockwise from top)
RADAR_AXES: list[tuple[str, str]] = [
    ("Chủ đạo", "so_chu_dao"),
    ("Sứ mệnh", "so_su_menh"),
    ("Linh hồn", "so_linh_hon"),
    ("Nhân cách", "so_nhan_cach"),
    ("Thái độ", "so_thai_do"),
    ("Trưởng thành", "so_truong_thanh"),
]


def pt(cx: float, cy: float, r: float, deg: float) -> tuple[float, float]:
    """Polar→cartesian; angle measured clockwise from the top (12 o'clock)."""
    rad = math.radians(deg - 90)
    return cx + r * math.cos(rad), cy + r * math.sin(rad)


def n(v: float) -> str:
    """Compact number formatting for SVG coordinates."""
    return f"{v:.1f}".rstrip("0").rstrip(".")


def cap9(v: int) -> int:
    """Clamp a numerology value to the 1..9 radial scale (11/22/33 → 1-9)."""
    num = int(v)
    while num > 9:
        num = sum(int(d) for d in str(num))
    return max(0, min(9, num))
