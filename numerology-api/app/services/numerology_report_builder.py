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


def _gate(payload: Optional[dict], unlocked, key: str, *content_keys: str) -> Optional[dict]:
    """Null out paid content for a locked section so it never reaches the client.

    Keeps `code`/`title` (safe labels for the teaser) but strips the given
    `content_keys`, marking the section `locked`. Returns payload unchanged when
    `key` is unlocked. No-op on None payloads.
    """
    if payload is None:
        return None
    if key in unlocked:
        return payload
    for ck in content_keys:
        if ck in payload:
            payload[ck] = None
    payload["locked"] = True
    return payload


def build_report(
    full_name: str,
    birth_day: str,
    calc: dict,
    models: dict,
    unlocked,
) -> dict:
    """Assemble the focused-summary JSON report.

    Structure mirrors the result-page sections: hero (số chủ đạo), core numbers,
    life peaks, challenges, personal year/month, missing numbers, power chart.

    `unlocked` is the set of section keys the viewer may see in full (see
    report_entitlement_service). Locked sections have their content stripped and
    are flagged ``locked: true`` so paid interpretations never leave the server.
    """
    main = models.get("main_number_data")

    so_chu_dao = {
        "code": calc["so_chu_dao"],
        "compound": calc["so_chu_dao_compound"],  # dạng kép '13/4' (G6)
        "title": main.title if main else None,
        "content": main.content if main else None,
        # MainNumber carries 4 extra content facets (career, love, etc.)
        "content_2": getattr(main, "content_2", None) if main else None,
        "content_3": getattr(main, "content_3", None) if main else None,
        "content_4": getattr(main, "content_4", None) if main else None,
        "content_5": getattr(main, "content_5", None) if main else None,
    }
    # Hero has two independent gates: the main interpretation ("so_chu_dao") and
    # the 4 deep-dive facets ("so_chu_dao_extra"). They use separate flags so a
    # free viewer can read the headline (locked=False) while the facets stay
    # locked (extra_locked=True) — a single shared flag would mislabel the hero.
    if "so_chu_dao" not in unlocked:
        so_chu_dao["content"] = None
        so_chu_dao["locked"] = True
    if "so_chu_dao_extra" not in unlocked:
        for ck in ("content_2", "content_3", "content_4", "content_5"):
            so_chu_dao[ck] = None
        so_chu_dao["extra_locked"] = True

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
    # Each core number gated by its own section key (su_menh, linh_hon, ...).
    core_numbers = {
        key: _gate(_row(models.get(model_key), code), unlocked, key, "content")
        for key, (model_key, code) in core_map.items()
    }

    # 4 life peaks (đỉnh cao) — each with the age it begins; gated as a block.
    peaks = [
        _gate(
            {
                "stage": i,
                "age_start": calc[f"tuoi_dinh_cao_{i}"],
                **_row(models.get(f"life_peak_{i}"), calc[f"dinh_cao_{i}"]),
            },
            unlocked,
            "peaks",
            "content",
        )
        for i in range(1, 5)
    ]

    # 4 challenges (thử thách) — gated as a block.
    challenges = [
        _gate(
            {"stage": i, **_row(models.get(f"challenge_life_{i}"), calc[f"thu_thach_{i}"])},
            unlocked,
            "challenges",
            "content",
        )
        for i in range(1, 5)
    ]

    personal = {
        "nam_ca_nhan": _gate(
            _row(models.get("personal_year_number"), calc["so_nam_ca_nhan"]),
            unlocked, "personal", "content",
        ),  # G2
        "thang_ca_nhan": _gate(
            _row(models.get("personal_month_number"), calc["so_thang_ca_nhan"]),
            unlocked, "personal", "content",
        ),
    }

    # Missing numbers (số thiếu) — MissNumber rows fetched as a list
    miss_rows = models.get("miss_number") or []
    missing_numbers = [
        _gate(_row(r, r.code), unlocked, "missing", "content") for r in miss_rows
    ]

    # Số Nợ Nghiệp (G1) — karmic-debt rows; code shown as compound 'code/single'
    karmic_debt = [
        _gate(
            {"code": r.code, "title": r.title, "content": r.content},
            unlocked, "karmic", "content",
        )
        for r in (models.get("karmic_debt") or [])
    ]
    # Biểu đồ tên (G3) — NameChart rows for digits present in the name
    name_chart = [
        _gate(_row(r, r.code), unlocked, "name_chart", "content")
        for r in (models.get("name_chart") or [])
    ]

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
        "karmic_debt": karmic_debt,
        "name_chart": name_chart,
        "arrows": {
            "present": calc["arrows_present"],
            "empty": calc["arrows_empty"],
            "isolated": calc["isolated"],
        },
        "power_chart": {
            "birth": _digit_counts(birth_day),
            "name": _digit_counts(calc["text_name"]),
            "combined": {
                str(d): birth_day.count(str(d)) + calc["text_name"].count(str(d))
                for d in range(1, 10)
            },
        },
    }
