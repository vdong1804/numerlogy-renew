"""Shared prompt templates for report illustrations (archetypes + per-user covers).

AI renders ABSTRACT ART ONLY — never text (all labels are overlaid by the
templates), so Vietnamese/master-number text is never garbled by the image model.
Used by both scripts/gen_report_assets.py (static library) and
app/services/cover_generator.py (per-user covers) → single source of truth.
"""

from __future__ import annotations

# Shared visual skeleton — keeps the whole set consistent (navy + gold mystical).
STYLE = (
    "Mystical numerology archetype illustration. Deep midnight navy-blue "
    "background with luminous antique-gold linework, sacred geometry, faint "
    "constellations and concentric celestial rings, soft ethereal glow. "
    "Symmetrical, centered, premium spiritual/cosmic aesthetic, elegant and "
    "minimal. The image must contain absolutely NO text, NO letters, NO numbers, "
    "NO digits, NO words, NO captions, NO labels, NO writing of any kind, and NO "
    "human faces — purely abstract ornament. Flat vector-meets-cosmic illustration."
)

# Per-number motif (Pythagorean archetype). Keys are str(Số chủ đạo).
MOTIFS: dict[str, str] = {
    "1": "a solitary radiant pillar of light ascending, a single sun ray, pioneering leadership",
    "2": "two mirrored crescent moons in gentle balance, intertwined harmony and duality",
    "3": "three interlocking blossoming arcs, creative flourish, joyful artistic expression",
    "4": "a grounded square foundation of four pillars, stable cubic sacred geometry, order",
    "5": "a five-pointed star caught mid-spiral, dynamic motion, freedom and adventure",
    "6": "a blooming rose mandala within a hexagon, nurturing love, warmth and home",
    "7": "an all-seeing eye inside a seven-pointed star above a lotus, mystic wisdom",
    "8": "an infinity ouroboros loop within an octagonal mandala, abundance and power",
    "9": "a radiant nine-petalled lotus enclosed in a circle, compassion and completion",
    "11": "twin luminous parallel pillars of light, heightened intuition and illumination",
    "22": "a grand architectural temple mandala, master builder geometry, manifestation",
}

_GENERIC_MOTIF = "a balanced cosmic mandala of sacred geometry"


def build_archetype_prompt(n: int | str) -> str:
    """Prompt for a square Số chủ đạo archetype emblem."""
    motif = MOTIFS.get(str(n), _GENERIC_MOTIF)
    return f"{STYLE} The central emblem evokes {motif}."


def build_cover_prompt(n: int | str | None = None) -> str:
    """Prompt for a vertical report-cover background (dark, text-safe).

    Pass a Số chủ đạo to theme it; omit for the generic static fallback cover.
    """
    motif = MOTIFS.get(str(n), _GENERIC_MOTIF) if n is not None else _GENERIC_MOTIF
    return (
        f"{STYLE} A sweeping cosmic night sky with a faint golden sacred-geometry "
        f"mandala glowing softly at the centre evoking {motif}, deep navy gradient, "
        "distant stars; dark and unobtrusive so overlaid text stays legible. "
        "Vertical poster composition."
    )
