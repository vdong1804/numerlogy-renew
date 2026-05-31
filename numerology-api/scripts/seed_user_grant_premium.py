"""Seed a paid Premium package order for a specific user.

Usage:
    python -m scripts.seed_user_grant_premium [EMAIL]

Defaults to vdong1804@gmail.com if no email is provided.

What it does (idempotent enough for repeated runs — each call creates a new
"paid" order + UserPackage row; safe to grant the same user more quota):
  1. Look up user by email (error if missing)
  2. Look up Product where sku='pkg-premium' (error if missing — run seed_products first)
  3. Build a paid Order + OrderItem with total_amount = product.price (snapshot)
  4. Call fulfillment_service.fulfill_order — grants UserPackage + bumps
     UserProfile.number_download quota
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.db.models.order import Order, OrderItem
from app.db.models.product import Product
from app.db.models.user import User
from app.services import fulfillment_service
from app.utils.ref_code import generate_ref_code
from scripts._db import get_session

DEFAULT_EMAIL = "vdong1804@gmail.com"
TARGET_SKU = "pkg-premium"


async def main(email: str) -> int:
    async with get_session() as db:
        # 1. User
        user_q = await db.execute(select(User).where(User.email == email))
        user = user_q.scalar_one_or_none()
        if user is None:
            print(f"  [ERROR] User not found: {email}", file=sys.stderr)
            return 1

        # 2. Product
        prod_q = await db.execute(
            select(Product).where(Product.sku == TARGET_SKU, Product.is_active.is_(True))
        )
        product = prod_q.scalar_one_or_none()
        if product is None:
            print(
                f"  [ERROR] Product '{TARGET_SKU}' not found / inactive. "
                "Run `python -m scripts.seed_products` first.",
                file=sys.stderr,
            )
            return 1

        # 3. Build paid order
        now = datetime.now(timezone.utc)
        order = Order(
            user_id=user.id,
            ref_code=generate_ref_code(),
            total_amount=product.price,
            currency="VND",
            status="paid",
            payment_method="manual-seed",
            expires_at=now + timedelta(days=1),
            paid_at=now,
            meta={"source": "seed_user_grant_premium"},
        )
        order.items.append(
            OrderItem(
                product_id=product.id,
                qty=1,
                unit_price=product.price,
                snapshot_name=product.name,
            )
        )
        db.add(order)
        await db.flush()
        print(
            f"  [INSERT] Order id={order.id} ref={order.ref_code} "
            f"user={user.email} product={product.sku} amount={product.price}"
        )

        # 4. Fulfill (grants UserPackage + bumps quota)
        await fulfillment_service.fulfill_order(db, order)
        await db.commit()

        print(
            f"  Done. Granted '{product.name}' "
            f"(quota={product.quota}, renewal_days={product.renewal_days}) "
            f"to {user.email}"
        )
        return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    target_email = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_EMAIL
    sys.exit(asyncio.run(main(target_email)))
