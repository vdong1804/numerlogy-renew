"""Seed chat add-on packages (Flash + Pro tiers).

Chat add-on packages live in the same `packages` table as PDF download packages,
distinguished by `package_kind='chat_addon'`. Each carries `message_count`,
`tier` (flash|pro), `validity_days`, and a marketing `content` (description).

Idempotent: check-then-insert by (name, package_kind='chat_addon'). Existing
rows are left untouched — to update fields, delete the row first.

Run: python -m scripts.seed_chat_addons
"""

import asyncio
import sys

from sqlalchemy import and_, select

from app.db.models.package import Package
from scripts._db import get_session

# ---------------------------------------------------------------------------
# Package catalogue
# ---------------------------------------------------------------------------
# Tiers:
#   - flash: fast, lightweight model — daily questions, quick lookups
#   - pro:   deeper analysis model    — chart interpretation, detailed reads
#
# `price_sale` < `price` triggers strikethrough display on the frontend.

CHAT_ADDONS = [
    {
        "name": "Flash Starter",
        "price": 29_000.0,
        "price_sale": 0.0,
        "number_download": 0,
        "package_kind": "chat_addon",
        "message_count": 50,
        "tier": "flash",
        "validity_days": 7,
        "content": (
            "50 tin nhắn Flash · hiệu lực 7 ngày. "
            "Phù hợp dùng thử và hỏi đáp nhanh."
        ),
    },
    {
        "name": "Flash Plus",
        "price": 99_000.0,
        "price_sale": 79_000.0,
        "number_download": 0,
        "package_kind": "chat_addon",
        "message_count": 200,
        "tier": "flash",
        "validity_days": 30,
        "content": (
            "200 tin nhắn Flash · hiệu lực 30 ngày. "
            "Tiết kiệm 20% — lựa chọn cho người dùng thường xuyên."
        ),
    },
    {
        "name": "Pro Standard",
        "price": 199_000.0,
        "price_sale": 0.0,
        "number_download": 0,
        "package_kind": "chat_addon",
        "message_count": 100,
        "tier": "pro",
        "validity_days": 30,
        "content": (
            "100 tin nhắn Pro · hiệu lực 30 ngày. "
            "Mô hình phân tích chuyên sâu, trả lời chi tiết hơn."
        ),
    },
    {
        "name": "Pro Plus",
        "price": 499_000.0,
        "price_sale": 449_000.0,
        "number_download": 0,
        "package_kind": "chat_addon",
        "message_count": 300,
        "tier": "pro",
        "validity_days": 60,
        "content": (
            "300 tin nhắn Pro · hiệu lực 60 ngày. "
            "Phù hợp giải nghĩa biểu đồ thần số học và tư vấn dài hạn."
        ),
    },
    {
        "name": "Pro Unlimited",
        "price": 999_000.0,
        "price_sale": 899_000.0,
        "number_download": 0,
        "package_kind": "chat_addon",
        "message_count": 1_000,
        "tier": "pro",
        "validity_days": 90,
        "content": (
            "1.000 tin nhắn Pro · hiệu lực 90 ngày. "
            "Gói trọn gói cho học viên và nhà tư vấn chuyên nghiệp."
        ),
    },
]


async def main() -> int:
    """Insert missing chat add-on packages. Returns count of newly inserted rows."""
    inserted = 0
    async with get_session() as db:
        for pkg in CHAT_ADDONS:
            result = await db.execute(
                select(Package).where(
                    and_(
                        Package.name == pkg["name"],
                        Package.package_kind == "chat_addon",
                    )
                )
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                db.add(Package(**pkg))
                inserted += 1
                print(f"  [INSERT] ChatAddon: {pkg['name']:<16} ({pkg['tier']}, {pkg['message_count']} msgs)")
            else:
                print(f"  [SKIP]   ChatAddon: {pkg['name']:<16} (exists id={existing.id})")
        await db.commit()
    print(f"  ChatAddons: {inserted} inserted, {len(CHAT_ADDONS) - inserted} skipped")
    return inserted


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    asyncio.run(main())
