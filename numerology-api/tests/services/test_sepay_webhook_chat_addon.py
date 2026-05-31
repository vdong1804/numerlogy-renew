# ruff: noqa: UP017, I001
"""Tests for SePay webhook → chat addon fulfillment (C1 fix).

Covers:
- CHATADDON<id> content triggers approve_payment and creates ChatAddonPurchase
- Idempotency: already-approved payment is skipped (duplicate)
- Unknown payment_id → unmatched
- Amount too low → amount_mismatch
"""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.models.chat.chat_addon_purchase import ChatAddonPurchase
from app.db.models.package import Package, UserPayment
from app.db.models.user import User
from app.schemas.webhook import SePayWebhookPayload
from app.services.sepay_service import parse_addon_payment_id, process_webhook


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _payload(content: str, amount: int = 49000, tx_id: int = 1001) -> SePayWebhookPayload:
    return SePayWebhookPayload(
        id=tx_id,
        content=content,
        transferType="in",
        transferAmount=amount,
    )


def _make_user(email: str = "sepay_addon@test.com") -> User:
    return User(
        email=email,
        hashed_password=hash_password("x"),
        first_name="Sepay",
        last_name="Test",
        is_active=True,
    )


def _make_addon_package() -> Package:
    return Package(
        name="Test Addon",
        price=49000,
        price_sale=49000,
        number_download=0,
        package_kind="chat_addon",
        message_count=50,
        tier="pro",
        validity_days=30,
    )


def _make_pending_payment(user_id: int, package_id: int, price: float = 49000) -> UserPayment:
    return UserPayment(user_id=user_id, package_id=package_id, price=price, status=1)


# ---------------------------------------------------------------------------
# parse_addon_payment_id unit tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text,expected",
    [
        ("CHATADDON123", 123),
        ("Noi dung CHATADDON456 thanh toan", 456),
        ("chataddon789", 789),  # case-insensitive
        ("ChatAddon42", 42),
        ("NSQ-ABCDEFGH no addon here", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_addon_payment_id(text, expected):
    assert parse_addon_payment_id(text) == expected


# ---------------------------------------------------------------------------
# Integration tests — process_webhook with CHATADDON content
# ---------------------------------------------------------------------------


class TestWebhookChatAddonFulfillment:
    async def test_webhook_matches_chataddon_content_and_fulfills(
        self, db_session: AsyncSession
    ):
        """Pending payment + chat_addon package → after webhook: payment.status=2,
        ChatAddonPurchase row created."""
        user = _make_user("addon_webhook_ok@test.com")
        pkg = _make_addon_package()
        db_session.add(user)
        db_session.add(pkg)
        await db_session.flush()

        payment = _make_pending_payment(user.id, pkg.id, price=49000)
        db_session.add(payment)
        await db_session.flush()
        await db_session.refresh(payment)

        payload = _payload(f"CHATADDON{payment.id}", amount=49000, tx_id=2001)
        event = await process_webhook(db_session, payload)
        await db_session.flush()

        assert event.status == "matched"

        await db_session.refresh(payment)
        assert payment.status == 2  # approved

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

    async def test_webhook_chataddon_idempotent_on_already_approved(
        self, db_session: AsyncSession
    ):
        """Payment already status=2 → webhook returns duplicate, does NOT re-fulfill."""
        user = _make_user("addon_webhook_dup@test.com")
        pkg = _make_addon_package()
        db_session.add(user)
        db_session.add(pkg)
        await db_session.flush()

        # Payment already approved
        payment = UserPayment(
            user_id=user.id, package_id=pkg.id, price=49000, status=2
        )
        db_session.add(payment)
        await db_session.flush()
        await db_session.refresh(payment)

        payload = _payload(f"CHATADDON{payment.id}", amount=49000, tx_id=2002)
        event = await process_webhook(db_session, payload)

        assert event.status == "duplicate"

        # No ChatAddonPurchase should be created
        result = await db_session.execute(
            select(ChatAddonPurchase).where(ChatAddonPurchase.user_id == user.id)
        )
        assert result.scalar_one_or_none() is None

    async def test_webhook_chataddon_unknown_payment_id_unmatched(
        self, db_session: AsyncSession
    ):
        """CHATADDON<nonexistent_id> → unmatched event."""
        payload = _payload("CHATADDON999999", amount=49000, tx_id=2003)
        event = await process_webhook(db_session, payload)
        assert event.status == "unmatched"
        assert "999999" in (event.error_message or "")

    async def test_webhook_chataddon_amount_too_low_rejected(
        self, db_session: AsyncSession
    ):
        """Transfer amount significantly below payment.price → amount_mismatch."""
        user = _make_user("addon_webhook_low@test.com")
        pkg = _make_addon_package()
        db_session.add(user)
        db_session.add(pkg)
        await db_session.flush()

        payment = _make_pending_payment(user.id, pkg.id, price=49000)
        db_session.add(payment)
        await db_session.flush()
        await db_session.refresh(payment)

        # Pay only 1000 VND — well below tolerance (1000 VND default)
        payload = _payload(f"CHATADDON{payment.id}", amount=1000, tx_id=2004)
        event = await process_webhook(db_session, payload)
        assert event.status == "amount_mismatch"

        # Payment still pending — not approved
        await db_session.refresh(payment)
        assert payment.status == 1

    async def test_webhook_no_marker_unmatched(self, db_session: AsyncSession):
        """Content without NSQ- or CHATADDON → unmatched."""
        payload = _payload("chuyen khoan thang 5", tx_id=2005)
        event = await process_webhook(db_session, payload)
        assert event.status == "unmatched"
