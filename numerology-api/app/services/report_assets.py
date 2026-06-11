"""Resolve static report illustration paths (archetypes + cover fallback).

Pure path helpers — no I/O at import. Returns paths *relative to the project
root* (WeasyPrint resolves them against base_url = project root). Returns None
when the asset file is absent, so templates degrade gracefully (no broken img).

Assets are generated once into static/report-assets/ (see
scripts/gen_report_assets.py). Same archetype is reused for every report with
the same Số chủ đạo (DRY — not generated per user).
"""

from __future__ import annotations

from pathlib import Path

# static/report-assets/ on disk (project_root/static/report-assets)
_ROOT = Path(__file__).resolve().parent.parent.parent
_ASSETS = _ROOT / "static" / "report-assets"

# Số chủ đạo values that have a dedicated archetype illustration
_ARCHETYPES = frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 22})


def archetype_image(so_chu_dao: int) -> str | None:
    """Relative path to the archetype illustration for a Số chủ đạo, else None."""
    if so_chu_dao not in _ARCHETYPES:
        return None
    rel = f"static/report-assets/archetypes/{so_chu_dao}.jpg"
    return rel if (_ROOT / rel).exists() else None


def cover_fallback() -> str | None:
    """Relative path to the default (static) cover background art, else None."""
    rel = "static/report-assets/cover/cover-fallback.jpg"
    return rel if (_ROOT / rel).exists() else None
