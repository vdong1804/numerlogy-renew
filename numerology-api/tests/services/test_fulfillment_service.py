# ruff: noqa: UP017, E501, I001
"""Tests for payment_service.approve_payment branching on package_kind.

Covers:
- chat_addon package → ChatAddonPurchase created, payment approved
- chat_addon idempotency — second approve_payment call with same payment_id safe
- pdf_download package → UserPackage created, download quota incremented (regression)
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.chat.chat_addon_purchase import ChatAddonPurchase
from app.db.models.package import Package, UserPackage, UserPayment
from app.db.models.user import User, UserProfile
from app.services.payment_service import approve_payment


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(email: str = "pay@test.com") -> User:
    from app.core.security import hash_password
    return User(
        email=email,
        hashed_password=hash_password("x"),
        first_name="Pay",
        last_name="Test",
        is_active=True,
    )


def _make_addon_package(
    name: str = "Basic Addon",
    message_count: int = 50,
    tier: str = "pro",
    validity_days: int = 30,
) -> Package:
    return Package(
        name=name,
        price=49000,
        price_sale=49000,
        number_download=0,
        package_kind="chat_addon",
        message_count=message_count,
        tier=tier,
        validity_days=validity_days,
    )


def _make_pdf_package(name: str = "PDF Pack", downloads: int = 5) -> Package:
    return Package(
        name=name,
        price=99000,
        price_sale=99000,
        number_download=downloads,
        package_kind="pdf_download",
    )


def _make_pending_payment(user_id: int, package_id: int, price: float = 49000) -> UserPayment:
    return UserPayment(
        user_id=user_id,
        package_id=package_id,
        price=price,
        status=1,  # pending
    )


# ---------------------------------------------------------------------------
# chat_addon fulfillment
# ---------------------------------------------------------------------------


class TestFulfillChatAddonPayment:
    async def test_fulfill_chat_addon_package_creates_purchase_row(
        self, db_session: AsyncSession
    ):
        """Approving a chat_addon payment inserts a ChatAddonPurchase row."""
        user = _make_user("addon_create@test.com")
        pkg = _make_addon_package(message_count=50, tier="pro", validity_days=30)
        db_session.add(user)
        db_session.add(pkg)
        await db_session.flush()

        payment = _make_pending_payment(user.id, pkg.id)
        db_session.add(payment)
        await db_session.flush()

        approved = await approve_payment(db_session, payment.id)
        assert approved.status == 2

        result = await db_session.execute(
            select(ChatAddonPurchase).where(
                ChatAddonPurchase.user_id == user.id,
                ChatAddonPurchase.payment_id == payment.id,
            )
        )
        purchase = result.scalar_one_or_none()
        assert purchase is not None
        assert purchase.remaining_messages == 50
        assert purchase.tier == "pro"
        assert purchase.is_active is True
        # expires_at should be ~30 days from now.
        # SQLite returns naive datetimes; strip tzinfo for portable comparison.
        now_naive = datetime.utcnow()
        expires = purchase.expires_at.replace(tzinfo=None) if purchase.expires_at.tzinfo else purchase.expires_at
        assert expires > now_naive + timedelta(days=28)
        assert expires < now_naive + timedelta(days=32)

    async def test_fulfill_chat_addon_idempotent_on_duplicate_payment(
        self, db_session: AsyncSession
    ):
        """Calling approve_payment twice raises 400 on second call (already processed).

        The idempotency guard in approve_payment itself rejects status!=1 on the
        second call, so only one ChatAddonPurchase row is ever created.
        """
        user = _make_user("addon_idem@test.com")
        pkg = _make_addon_package(message_count=100)
        db_session.add(user)
        db_session.add(pkg)
        await db_session.flush()

        payment = _make_pending_payment(user.id, pkg.id)
        db_session.add(payment)
        await db_session.flush()

        # First call succeeds
        await approve_payment(db_session, payment.id)

        # Second call must raise (payment already at status=2)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await approve_payment(db_session, payment.id)
        assert exc_info.value.status_code == 400

        # Only one purchase row exists
        result = await db_session.execute(
            select(ChatAddonPurchase).where(ChatAddonPurchase.payment_id == payment.id)
        )
        purchases = result.scalars().all()
        assert len(purchases) == 1

    async def test_fulfill_addon_idempotent_via_fulfill_chat_addon_directly(
        self, db_session: AsyncSession
    ):
        """fulfill_chat_addon returns existing row on duplicate payment_id call."""
        from app.services.chat.addon_fulfillment import fulfill_chat_addon

        user = _make_user("addon_direct_idem@test.com")
        pkg = _make_addon_package(message_count=20)
        db_session.add(user)
        db_session.add(pkg)
        await db_session.flush()

        # Call once
        first = await fulfill_chat_addon(db_session, user_id=user.id, package=pkg, payment_id=42)
        await db_session.flush()

        # Call again with same payment_id
        second = await fulfill_chat_addon(db_session, user_id=user.id, package=pkg, payment_id=42)

        assert first.id == second.id

        # Still only one row
        result = await db_session.execute(
            select(ChatAddonPurchase).where(ChatAddonPurchase.payment_id == 42)
        )
        assert len(result.scalars().all()) == 1


# ---------------------------------------------------------------------------
# pdf_download fulfillment (regression)
# ---------------------------------------------------------------------------


class TestFulfillPdfDownloadPayment:
    async def test_fulfill_pdf_download_unchanged(self, db_session: AsyncSession):
        """Approving a pdf_download payment still creates UserPackage + grants quota."""
        user = _make_user("pdf_fulfill@test.com")
        pkg = _make_pdf_package(downloads=5)
        db_session.add(user)
        db_session.add(pkg)
        await db_session.flush()

        profile = UserProfile(
            user_id=user.id,
            name="PDF User",
            birth_day="01011990",
            number_download=0,
        )
        db_session.add(profile)
        await db_session.flush()

        payment = _make_pending_payment(user.id, pkg.id, price=99000)
        db_session.add(payment)
        await db_session.flush()

        approved = await approve_payment(db_session, payment.id)
        assert approved.status == 2

        # UserPackage created
        pkg_result = await db_session.execute(
            select(UserPackage).where(
                UserPackage.user_id == user.id,
                UserPackage.package_id == pkg.id,
                UserPackage.is_used == True,  # noqa: E712
            )
        )
        user_pkg = pkg_result.scalar_one_or_none()
        assert user_pkg is not None

        # Download quota incremented
        await db_session.refresh(profile)
        assert profile.number_download == 5

        # No ChatAddonPurchase created
        addon_result = await db_session.execute(
            select(ChatAddonPurchase).where(ChatAddonPurchase.user_id == user.id)
        )
        assert addon_result.scalar_one_or_none() is None
