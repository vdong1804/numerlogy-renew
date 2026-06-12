"""Pythagoras birth-chart derivations: arrows, isolated numbers, karmic debt.

Pure math — no I/O. Split from numerology.py to keep that file ≤200 lines.
Layout (Pythagoras grid, top→bottom):
    3 6 9
    2 5 8
    1 4 7

Consumed by app.core.numerology.calculate_numerology_numbers.
"""

from __future__ import annotations

# 8 chart lines: 3 rows (physical/soul/mind), 3 columns, 2 diagonals.
# Codes match the `birthday_chart` content table (e.g. "147", "not_147").
LINES: list[str] = ["147", "258", "369", "123", "456", "789", "159", "357"]

# Corner numbers that can become "lẻ loi/đơn độc" (isolated) and the
# adjacent cells (orthogonal + diagonal toward centre) that, if all empty,
# leave the corner isolated. Rules per SAMPLE docx.
NEIGHBORS: dict[int, set[str]] = {
    1: {"2", "4", "5"},
    3: {"2", "5", "6"},
    7: {"4", "5", "8"},
    9: {"5", "6", "8"},
}

KARMIC: set[int] = {13, 14, 16, 19}  # Số Nợ Nghiệp codes


def compute_arrows(present: set[str]) -> tuple[list[str], list[str]]:
    """Return (strength_codes, empty_codes) for the 8 chart lines.

    strength: every digit of the line is present in the DOB → code "147".
    empty:    every digit of the line is absent → code "not_147".
    """
    strength: list[str] = []
    empty: list[str] = []
    for line in LINES:
        digits = set(line)
        if digits <= present:
            strength.append(line)
        elif digits.isdisjoint(present):
            empty.append(f"not_{line}")
    return strength, empty


def compute_isolated(present: set[str]) -> list[int]:
    """Return corner numbers that are present but cut off from neighbours."""
    return [
        d for d, neigh in NEIGHBORS.items()
        if str(d) in present and neigh.isdisjoint(present)
    ]


def detect_karmic_debt(total: int) -> int | None:
    """Return the karmic-debt code (13/14/16/19) on the reduction path, else None.

    A core number carries karmic debt when its total passes through a karmic
    two-digit value on the way down to a single digit.
    """
    n = int(total)
    while n > 9:
        if n in KARMIC:
            return n
        n = sum(int(d) for d in str(n))
    return None


def compound_str(total: int) -> str:
    """Display số chủ đạo as 'master/single' (11/2, 22/4, 33/6); single digit otherwise.

    Only master numbers 11/22/33 carry a compound form. A non-master penultimate
    (e.g. 24 → 6, 13 → 4) reduces straight to its single digit — no '24/6'.
    """
    n = int(total)
    while n > 9:
        if n in (11, 22, 33):
            return f"{n}/{sum(int(d) for d in str(n))}"
        n = sum(int(d) for d in str(n))
    return str(n)


def derive_chart_fields(
    birth_day: str,
    text_name: str,
    chu_dao_total: int,
    sum_full_name: int,
    sum_full_vowel: int,
    sum_full_consonant: int,
) -> dict:
    """Bundle all birth/name-chart report fields (G1-G6) in one call.

    Keeps calculate_numerology_numbers lean; takes the already-computed letter
    sums so the karmic-debt scan covers the 5 core numbers.
    """
    dob_present = {c for c in birth_day if c in "123456789"}
    arrows_present, arrows_empty = compute_arrows(dob_present)

    # Số Nợ Nghiệp (G1): karmic debt across 5 cores, sorted ascending.
    no_nghiep = sorted({
        d for d in (
            detect_karmic_debt(chu_dao_total),         # Chủ Đạo
            detect_karmic_debt(int(birth_day[0:2])),   # Ngày Sinh (day-of-month)
            detect_karmic_debt(sum_full_name),         # Sứ Mệnh
            detect_karmic_debt(sum_full_vowel),        # Linh Hồn
            detect_karmic_debt(sum_full_consonant),    # Nhân Cách
        ) if d
    })
    return {
        "arrows_present": arrows_present,
        "arrows_empty": arrows_empty,
        "isolated": compute_isolated(dob_present),
        "name_counts": {str(d): text_name.count(str(d)) for d in range(1, 10)},
        "no_nghiep": no_nghiep,
        "so_chu_dao_compound": compound_str(chu_dao_total),  # G6
    }
