"""Seed the new products catalogue.

- 3 quota packages (Free / Basic / Premium) — parallel to legacy `packages` table
- 3 paid standalone reports (overview / love / career)
- 1 free lead-magnet report (report-mini-free)

Idempotent: uses SKU as the upsert key.
Run: python -m scripts.seed_products
"""

import asyncio
import sys

from sqlalchemy import select

from app.db.models.product import Product
from scripts._db import get_session

PRODUCTS = [
    # Quota packages
    {
        "sku": "pkg-free",
        "type": "package",
        "name": "Goi Free",
        "slug": "goi-free",
        "description": "1 ban bao cao mien phi de trai nghiem",
        "price": 0,
        "quota": 1,
        "renewal_days": None,
        "sort_order": 10,
    },
    {
        "sku": "pkg-basic",
        "type": "package",
        "name": "Goi Basic",
        "slug": "goi-basic",
        "description": "3 ban bao cao trong 30 ngay",
        "price": 99000,
        "quota": 3,
        "renewal_days": 30,
        "sort_order": 20,
    },
    {
        "sku": "pkg-premium",
        "type": "package",
        "name": "Goi Premium",
        "slug": "goi-premium",
        "description": "10 ban bao cao trong 30 ngay",
        "price": 299000,
        "quota": 10,
        "renewal_days": 30,
        "sort_order": 30,
    },
    # Standalone paid reports
    {
        "sku": "report-overview",
        "type": "report",
        "name": "Bao cao Tong quan",
        "slug": "bao-cao-tong-quan",
        "description": "Phan tich tong the cac chi so quan trong cua ban",
        "price": 99000,
        "template_name": "report-overview.html",
        "content_codes": [
            "main_number",
            "souls_number",
            "mission_number",
            "execution_number",
        ],
        "sort_order": 40,
    },
    {
        "sku": "report-love",
        "type": "report",
        "name": "Bao cao Tinh duyen",
        "slug": "bao-cao-tinh-duyen",
        "description": "Phan tich tinh yeu va moi quan he",
        "price": 149000,
        "template_name": "report-love.html",
        "content_codes": ["souls_number", "personal_year_number", "attitude_number"],
        "sort_order": 50,
    },
    {
        "sku": "report-career",
        "type": "report",
        "name": "Bao cao Su nghiep",
        "slug": "bao-cao-su-nghiep",
        "description": "Phan tich con duong su nghiep va tai loc",
        "price": 149000,
        "template_name": "report-career.html",
        "content_codes": ["main_number", "mature_number", "peak_life"],
        "sort_order": 60,
    },
    # Free lead-magnet (one per user — enforced at app layer in phase 2)
    {
        "sku": "report-mini-free",
        "type": "report",
        "name": "Bao cao Mini (Free)",
        "slug": "bao-cao-mini-free",
        "description": "Ban xem thu mien phi mot lan",
        "price": 0,
        "template_name": "report-mini.html",
        "content_codes": ["main_number"],
        "sort_order": 5,
    },
]


async def main() -> int:
    """Upsert products by SKU. Returns count of newly inserted rows."""
    inserted = 0
    async with get_session() as db:
        for spec in PRODUCTS:
            result = await db.execute(select(Product).where(Product.sku == spec["sku"]))
            existing = result.scalar_one_or_none()
            if existing is None:
                db.add(Product(**spec))
                inserted += 1
                print(f"  [INSERT] {spec['sku']:<20} {spec['name']}")
            else:
                # Update mutable fields only (keep id/sku stable)
                for k, v in spec.items():
                    if k == "sku":
                        continue
                    setattr(existing, k, v)
                print(f"  [UPDATE] {spec['sku']:<20} {spec['name']}")
        await db.commit()
    print(f"  Products: {inserted} inserted, {len(PRODUCTS) - inserted} updated")
    return inserted


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    asyncio.run(main())
