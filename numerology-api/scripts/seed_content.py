"""Seed all 22 numerology content tables with placeholder rows.

Idempotent: uses INSERT ... ON CONFLICT (code) DO NOTHING.
Run: python -m scripts.seed_content
"""

import asyncio
import sys

from sqlalchemy.dialects.postgresql import insert

from app.db.models.numerology_content import (
    AttitudeNumber,
    BalanceNumber,
    BirthdayChart,
    BirthdayNumber,
    ChallengeLife,
    DeficitNumber,
    DevelopmentNumber,
    ExecutionNumber,
    Identifiable,
    IntrospectiveNumber,
    KarmicNumber,
    LifePeak,
    MainNumber,
    MatureNumber,
    MissNumber,
    MissionNumber,
    NameChart,
    PersonalMonthNumber,
    PersonalYearNumber,
    PhoneNumber,
    SoulsNumber,
    StagesOfLife,
)
from scripts._content_codes import CONTENT_CODES
from scripts._db import get_session

# Map model name → ORM class (same order as CONTENT_CODES keys)
_MODEL_MAP = {
    "MainNumber":           MainNumber,
    "MissionNumber":        MissionNumber,
    "ExecutionNumber":      ExecutionNumber,
    "SoulsNumber":          SoulsNumber,
    "DevelopmentNumber":    DevelopmentNumber,
    "LifePeak":             LifePeak,
    "ChallengeLife":        ChallengeLife,
    "BirthdayChart":        BirthdayChart,
    "NameChart":            NameChart,
    "StagesOfLife":         StagesOfLife,
    "AttitudeNumber":       AttitudeNumber,
    "BirthdayNumber":       BirthdayNumber,
    "MatureNumber":         MatureNumber,
    "IntrospectiveNumber":  IntrospectiveNumber,
    "KarmicNumber":         KarmicNumber,
    "DeficitNumber":        DeficitNumber,
    "PhoneNumber":          PhoneNumber,
    "PersonalMonthNumber":  PersonalMonthNumber,
    "Identifiable":         Identifiable,
    "BalanceNumber":        BalanceNumber,
    "MissNumber":           MissNumber,
    "PersonalYearNumber":   PersonalYearNumber,
}


def _build_rows(model_name: str, codes: list[str]) -> list[dict]:
    """Build insert dicts for a given model and its code list."""
    rows = []
    for code in codes:
        title = f"{model_name} - Code {code}"
        content = (
            f"<p>Noi dung placeholder cho {model_name} ma {code}. "
            f"Vui long cap nhat qua admin.</p>"
        )
        row: dict = {"code": code, "title": title, "content": content, "number_page": None}
        # MainNumber has extra content_2..5 columns — leave None (nullable)
        if model_name == "MainNumber":
            row.update({"content_2": None, "content_3": None, "content_4": None, "content_5": None})
        rows.append(row)
    return rows


async def seed_table(model_name: str, model_cls, codes: list[str]) -> int:
    """Insert rows for one table. Returns number of rows attempted."""
    rows = _build_rows(model_name, codes)
    async with get_session() as db:
        stmt = (
            insert(model_cls)
            .values(rows)
            .on_conflict_do_nothing(index_elements=["code"])
        )
        await db.execute(stmt)
        await db.commit()
    return len(rows)


async def main() -> dict[str, int]:
    """Seed all content tables. Returns {model_name: row_count}."""
    results: dict[str, int] = {}
    for model_name, codes in CONTENT_CODES.items():
        model_cls = _MODEL_MAP[model_name]
        count = await seed_table(model_name, model_cls, codes)
        results[model_name] = count
        print(f"  [OK] {model_name:<25} {count:>4} rows attempted")
    return results


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    asyncio.run(main())
