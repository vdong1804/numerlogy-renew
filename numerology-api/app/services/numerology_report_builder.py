"""Build a structured JSON numerology report from calc numbers + DB content rows.

Pure function — no DB, no async. Reuses the same `calc` dict produced by
`calculate_numerology_numbers()` and the `models` dict from `get_numerology_models()`,
so the JSON report stays consistent with the PDF/HTML report.

Consumed by GET /api/numerology-report (landing-page result screen).
"""

from __future__ import annotations

from typing import Any, Optional


def _row(row: Any, code: Any) -> Optional[dict]:
    """Serialize a numerology content ORM row to a plain dict.

    `code` is the computed numerology number (authoritative, always present even
    when the DB has no matching row — e.g. master-number edge cases).
    """
    if row is None:
        return {"code": code, "title": None, "content": None, "number_page": None}
    return {
        "code": code,
        "title": row.title,
        "content": row.content,
        "number_page": row.number_page,
    }


def _digit_counts(source: str) -> dict[str, int]:
    """Count occurrences of digits 1-9 in a string (for the power chart)."""
    return {str(d): source.count(str(d)) for d in range(1, 10)}


def build_report(
    full_name: str,
    birth_day: str,
    calc: dict,
    models: dict,
) -> dict:
    """Assemble the focused-summary JSON report.

    Structure mirrors the result-page sections: hero (số chủ đạo), core numbers,
    life peaks, challenges, personal year/month, missing numbers, power chart.
    """
    main = models.get("main_number_data")

    so_chu_dao = {
        "code": calc["so_chu_dao"],
        "title": main.title if main else None,
        "content": main.content if main else None,
        # MainNumber carries 4 extra content facets (career, love, etc.)
        "content_2": getattr(main, "content_2", None) if main else None,
        "content_3": getattr(main, "content_3", None) if main else None,
        "content_4": getattr(main, "content_4", None) if main else None,
        "content_5": getattr(main, "content_5", None) if main else None,
    }

    # Core numbers — key → (model dict key, computed calc number)
    core_map = {
        "su_menh": ("mission_number", calc["so_su_menh"]),
        "linh_hon": ("souls_number", calc["so_linh_hon"]),
        "nhan_cach": ("mature_number", calc["so_nhan_cach"]),
        "thai_do": ("attitude_number", calc["so_thai_do"]),
        "truong_thanh": ("development_number", calc["so_truong_thanh"]),
        "ngay_sinh": ("birth_number", calc["so_ngay_sinh"]),
        "noi_cam": ("karmic_number", calc["so_noi_cam"]),
    }
    core_numbers = {
        key: _row(models.get(model_key), code)
        for key, (model_key, code) in core_map.items()
    }

    # 4 life peaks (đỉnh cao) — each with the age it begins
    peaks = [
        {
            "stage": i,
            "age_start": calc[f"tuoi_dinh_cao_{i}"],
            **_row(models.get(f"life_peak_{i}"), calc[f"dinh_cao_{i}"]),
        }
        for i in range(1, 5)
    ]

    # 4 challenges (thử thách)
    challenges = [
        {
            "stage": i,
            **_row(models.get(f"challenge_life_{i}"), calc[f"thu_thach_{i}"]),
        }
        for i in range(1, 5)
    ]

    personal = {
        "thang_ca_nhan": _row(models.get("personal_month_number"), calc["so_thang_ca_nhan"]),
    }

    # Missing numbers (số thiếu) — MissNumber rows fetched as a list
    miss_rows = models.get("miss_number") or []
    missing_numbers = [_row(r, r.code) for r in miss_rows]

    return {
        "user": {
            "name": full_name,
            "birth_day_text": f"{birth_day[:2]}/{birth_day[2:4]}/{birth_day[4:]}",
            "age": calc["age"],
        },
        "so_chu_dao": so_chu_dao,
        "core_numbers": core_numbers,
        "peaks": peaks,
        "challenges": challenges,
        "personal": personal,
        "missing_numbers": missing_numbers,
        "power_chart": {
            "birth": _digit_counts(birth_day),
            "name": _digit_counts(calc["text_name"]),
        },
    }
