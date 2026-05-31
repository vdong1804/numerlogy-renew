# ruff: noqa: UP045, UP017
"""Fulfillment helper for chat_addon packages.

Called by fulfillment_service.fulfill_order when package.package_kind == 'chat_addon'.
Idempotent: a second call with the same payment_id returns the existing row.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.chat.chat_addon_purchase import ChatAddonPurchase
from app.db.models.package import Package

logger = logging.getLogger(__name__)


async def fulfill_chat_addon(
    db: AsyncSession,
    *,
    user_id: int,
    package: Package,
    payment_id: Optional[int],
) -> ChatAddonPurchase:
    """Insert a ChatAddonPurchase row and return it.

    Idempotency: if a row already exists for (payment_id), return it without
    a second insert — webhook may fire twice (matches existing fulfillment pattern).

    Raises ValueError if:
    - package.package_kind != 'chat_addon'
    - message_count / tier / validity_days are None
    """
    # Validate package kind
    if package.package_kind != "chat_addon":
        raise ValueError(
            f"fulfill_chat_addon called with package_kind={package.package_kind!r}; "
            "expected 'chat_addon'"
        )

    # Validate required addon fields
    if package.message_count is None:
        raise ValueError(f"Package {package.id} has NULL message_count")
    if package.tier is None:
        raise ValueError(f"Package {package.id} has NULL tier")
    if package.validity_days is None:
        raise ValueError(f"Package {package.id} has NULL validity_days")

    # Idempotency check — skip insert if payment_id already fulfilled
    if payment_id is not None:
        existing_q = await db.execute(
            select(ChatAddonPurchase).where(
                ChatAddonPurchase.payment_id == payment_id
            )
        )
        existing = existing_q.scalar_one_or_none()
        if existing is not None:
            logger.info(
                "fulfill_chat_addon: payment_id=%s already fulfilled (row %s), skipping",
                payment_id,
                existing.id,
            )
            return existing

    expires_at = datetime.now(timezone.utc) + timedelta(days=package.validity_days)

    purchase = ChatAddonPurchase(
        user_id=user_id,
        package_id=package.id,
        remaining_messages=package.message_count,
        tier=package.tier,
        payment_id=payment_id,
        expires_at=expires_at,
        is_active=True,
    )
    db.add(purchase)
    await db.flush()

    logger.info(
        "fulfill_chat_addon: created purchase %s for user %s (package %s, msgs=%s, tier=%s)",
        purchase.id,
        user_id,
        package.id,
        package.message_count,
        package.tier,
    )
    return purchase
