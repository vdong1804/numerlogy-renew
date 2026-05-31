"""Seed sample bank accounts.

Idempotent: check-then-insert by (bank + account_number).
Run: python -m scripts.seed_banks
"""

import asyncio
import sys

from sqlalchemy import select

from app.db.models.package import Bank
from scripts._db import get_session

BANKS = [
    {
        "bank": "Vietcombank",
        "branch": "Ho Chi Minh",
        "account_number": "1234567890",
        "account_holder": "Nguyen Sinh Quan",
        "code": "VCB",
        "image": None,
    },
]


async def main() -> int:
    """Insert missing banks. Returns count of newly inserted rows."""
    inserted = 0
    async with get_session() as db:
        for b in BANKS:
            result = await db.execute(
                select(Bank).where(
                    Bank.bank == b["bank"],
                    Bank.account_number == b["account_number"],
                )
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                db.add(Bank(**b))
                inserted += 1
                print(f"  [INSERT] Bank: {b['bank']} / {b['account_number']}")
            else:
                print(f"  [SKIP]   Bank: {b['bank']} (exists id={existing.id})")
        await db.commit()
    print(f"  Banks: {inserted} inserted, {len(BANKS) - inserted} skipped")
    return inserted


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    asyncio.run(main())
