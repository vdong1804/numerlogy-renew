"""Seed sample packages (Free / Basic / Premium).

Idempotent: check-then-insert (no unique constraint on name).
Run: python -m scripts.seed_packages
"""

import asyncio
import sys

from sqlalchemy import select

from app.db.models.package import Package
from scripts._db import get_session

PACKAGES = [
    {"name": "Free",    "price": 0.0,      "price_sale": 0.0,      "number_download": 1,  "content": "Goi mien phi"},
    {"name": "Basic",   "price": 99000.0,  "price_sale": 99000.0,  "number_download": 3,  "content": "Goi co ban"},
    {"name": "Premium", "price": 299000.0, "price_sale": 299000.0, "number_download": 10, "content": "Goi cao cap"},
]


async def main() -> int:
    """Insert missing packages. Returns count of newly inserted rows."""
    inserted = 0
    async with get_session() as db:
        for pkg in PACKAGES:
            result = await db.execute(select(Package).where(Package.name == pkg["name"]))
            existing = result.scalar_one_or_none()
            if existing is None:
                db.add(Package(**pkg))
                inserted += 1
                print(f"  [INSERT] Package: {pkg['name']}")
            else:
                print(f"  [SKIP]   Package: {pkg['name']} (exists id={existing.id})")
        await db.commit()
    print(f"  Packages: {inserted} inserted, {len(PACKAGES) - inserted} skipped")
    return inserted


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    asyncio.run(main())
