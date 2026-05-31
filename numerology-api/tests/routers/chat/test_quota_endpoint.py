# ruff: noqa: UP017
"""Integration tests for GET /api/chat/quota."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.chat.chat_addon_purchase import ChatAddonPurchase
from app.db.models.chat.quota_usage import ChatQuotaUsage
from app.db.models.package import Package


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _make_addon_package(db_session: AsyncSession) -> Package:
    pkg = Package(
        name="Pro Pack",
        price=49000,
        price_sale=49000,
        number_download=0,
        package_kind="chat_addon",
        message_count=50,
        tier="pro",
        validity_days=30,
    )
    db_session.add(pkg)
    return pkg


class TestQuotaEndpoint:
    async def test_quota_requires_auth(self, client):
        """Unauthenticated → 401."""
        resp = await client.get("/api/chat/quota")
        assert resp.status_code == 401

    async def test_quota_returns_full_balance_no_addon(
        self, client, auth_headers, user
    ):
        """Fresh user: free_used=0, addon_remaining=0, can_send=True, source=free."""
        resp = await client.get("/api/chat/quota", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]

        assert data["free_used_today"] == 0
        assert data["free_limit"] == 3
        assert data["addon_remaining"] == 0
        assert data["addon_tier"] is None
        assert data["can_send"] is True
        assert data["decision_source"] == "free"

    async def test_quota_after_2_sends(
        self, client, auth_headers, user, db_session: AsyncSession
    ):
        """Seed free_used=2 → can_send=True, free_used_today=2, 1 remaining."""
        today = datetime.now(timezone.utc).date()
        usage = ChatQuotaUsage(user_id=user.id, date=today, free_used=2, paid_used=0)
        db_session.add(usage)
        await db_session.commit()

        resp = await client.get("/api/chat/quota", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]

        assert data["free_used_today"] == 2
        assert data["free_limit"] == 3
        assert data["can_send"] is True
        assert data["decision_source"] == "free"

    async def test_quota_exhausted_free(
        self, client, auth_headers, user, db_session: AsyncSession
    ):
        """free_used=3 (at limit) → can_send=False, source=None."""
        today = datetime.now(timezone.utc).date()
        usage = ChatQuotaUsage(user_id=user.id, date=today, free_used=3, paid_used=0)
        db_session.add(usage)
        await db_session.commit()

        resp = await client.get("/api/chat/quota", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]

        assert data["can_send"] is False
        assert data["decision_source"] is None

    async def test_quota_with_active_addon(
        self, client, auth_headers, user, db_session: AsyncSession
    ):
        """Active addon: can_send=True, source=addon, addon_remaining>0."""
        pkg = _make_addon_package(db_session)
        await db_session.flush()

        # Exhaust free quota first — addon should take priority
        today = datetime.now(timezone.utc).date()
        usage = ChatQuotaUsage(user_id=user.id, date=today, free_used=3, paid_used=0)
        db_session.add(usage)

        addon = ChatAddonPurchase(
            user_id=user.id,
            package_id=pkg.id,
            remaining_messages=20,
            tier="pro",
            expires_at=_now() + timedelta(days=30),
            is_active=True,
        )
        db_session.add(addon)
        await db_session.commit()

        resp = await client.get("/api/chat/quota", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]

        assert data["can_send"] is True
        assert data["decision_source"] == "addon"
        assert data["addon_remaining"] == 20
        assert data["addon_tier"] == "pro"
        assert data["addon_expires_at"] is not None
