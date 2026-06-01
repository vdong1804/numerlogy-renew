"""Seed REAL Vietnamese numerology content into all report-related tables.

Overwrites placeholder rows via INSERT ... ON CONFLICT (code) DO UPDATE, so it
is idempotent and safe to re-run. Prose lives in scripts/_report_content_data.py
(DRY). Only seeds the tables that feed GET /api/numerology-report.

Run: python -m scripts.seed_report_content
"""

import asyncio
import sys

from sqlalchemy.dialects.postgresql import insert

from app.db.models.numerology_content import (
    AttitudeNumber,
    BalanceNumber,
    BirthdayNumber,
    ChallengeLife,
    DevelopmentNumber,
    ExecutionNumber,
    KarmicNumber,
    LifePeak,
    MainNumber,
    MatureNumber,
    MissNumber,
    MissionNumber,
    PersonalMonthNumber,
    PersonalYearNumber,
    SoulsNumber,
)
from scripts._db import get_session
from scripts._report_content_data import (
    INDICATOR_SPECS,
    LIFE_PEAK_INTRO,
    NUMBER_MEANINGS,
    PERSONAL_YEAR_SPECIAL,
)

# Map model class name (from INDICATOR_SPECS) → ORM class.
_MODEL_MAP = {
    "MainNumber": MainNumber,
    "MissionNumber": MissionNumber,
    "SoulsNumber": SoulsNumber,
    "MatureNumber": MatureNumber,
    "AttitudeNumber": AttitudeNumber,
    "BalanceNumber": BalanceNumber,
    "DevelopmentNumber": DevelopmentNumber,
    "BirthdayNumber": BirthdayNumber,
    "ExecutionNumber": ExecutionNumber,
    "KarmicNumber": KarmicNumber,
    "PersonalMonthNumber": PersonalMonthNumber,
    "MissNumber": MissNumber,
    "ChallengeLife": ChallengeLife,
    "PersonalYearNumber": PersonalYearNumber,
    "LifePeak": LifePeak,
}


def _p(text: str) -> str:
    """Wrap one prose block in a <p> tag."""
    return f"<p>{text}</p>"


def _compose(intro: str, fields: list[str], meaning: dict) -> str:
    """Build HTML content: intro paragraph + one <p> per framed field."""
    parts = [_p(intro)] + [_p(meaning[f]) for f in fields]
    return "".join(parts)


def _build_row(spec: dict, code: str) -> dict:
    """Turn (indicator spec, number code) → an upsert row dict."""
    label = spec["label"]
    intro = spec["intro"]
    fields = spec["fields"]

    # --- Special-case codes that have no NUMBER_MEANINGS entry ---
    if spec["model"] == "LifePeak" and code == "1000":
        return {
            "code": code,
            "value": None,
            "title": "Giới thiệu các đỉnh cao cuộc đời",
            "content": LIFE_PEAK_INTRO,
            "number_page": None,
        }
    if spec["model"] == "PersonalYearNumber" and code in PERSONAL_YEAR_SPECIAL:
        return {
            "code": code,
            "value": None,
            "title": f"{label} số {code}",
            "content": _p(intro) + _p(PERSONAL_YEAR_SPECIAL[code]),
            "number_page": None,
        }

    meaning = NUMBER_MEANINGS[code]
    row: dict = {
        "code": code,
        "value": None,
        "title": f"{label} số {code}",
        "content": _compose(intro, fields, meaning),
        "number_page": None,
    }

    # MainNumber carries 4 extra facets: career / love / talent / challenge.
    if spec["model"] == "MainNumber":
        row["content_2"] = _p(meaning["career"])
        row["content_3"] = _p(meaning["love"])
        row["content_4"] = _p(meaning["talent"])
        row["content_5"] = _p(meaning["challenge"])

    return row


async def seed_indicator(spec: dict) -> int:
    """Upsert all rows for one indicator's table. Returns row count."""
    model_cls = _MODEL_MAP[spec["model"]]
    rows = [_build_row(spec, code) for code in spec["codes"]]

    # Columns to overwrite on conflict (everything except the unique key + pk).
    update_cols = {"value", "title", "content", "number_page"}
    if spec["model"] == "MainNumber":
        update_cols |= {"content_2", "content_3", "content_4", "content_5"}

    async with get_session() as db:
        stmt = insert(model_cls).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["code"],
            set_={c: stmt.excluded[c] for c in update_cols},
        )
        await db.execute(stmt)
        await db.commit()
    return len(rows)


async def main() -> dict[str, int]:
    """Seed all report tables with real content. Returns {model: count}."""
    results: dict[str, int] = {}
    for name, spec in INDICATOR_SPECS.items():
        count = await seed_indicator(spec)
        results[name] = count
        print(f"  [OK] {spec['model']:<22} {count:>3} rows")
    total = sum(results.values())
    print(f"  Report content total: {total} rows across {len(results)} tables")
    return results


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    asyncio.run(main())
