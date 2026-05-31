# ruff: noqa: I001
"""Integration tests for GET /api/chat/addons and POST /api/chat/addons/{id}/purchase."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.package import Package


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_addon_package(
    name: str = "Basic Pack",
    price: float = 49000,
    message_count: int = 50,
    tier: str = "pro",
    validity_days: int = 30,
) -> Package:
    return Package(
        name=name,
        price=price,
        price_sale=price,
        number_download=0,
        package_kind="chat_addon",
        message_count=message_count,
        tier=tier,
        validity_days=validity_days,
    )


def _make_pdf_package(name: str = "PDF Pack") -> Package:
    return Package(
        name=name,
        price=99000,
        price_sale=99000,
        number_download=5,
        package_kind="pdf_download",
    )


# ---------------------------------------------------------------------------
# GET /api/chat/addons
# ---------------------------------------------------------------------------


class TestListAddonPackages:
    async def test_list_addons_returns_only_chat_addon_kind(
        self, client, auth_headers, db_session: AsyncSession
    ):
        """Only chat_addon packages appear; pdf_download is excluded."""
        addon = _make_addon_package(name="Chat Addon A")
        pdf = _make_pdf_package(name="PDF Only")
        db_session.add(addon)
        db_session.add(pdf)
        await db_session.commit()

        resp = await client.get("/api/chat/addons", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        names = [p["name"] for p in data]
        assert "Chat Addon A" in names
        assert "PDF Only" not in names

    async def test_list_addons_returns_correct_fields(
        self, client, auth_headers, db_session: AsyncSession
    ):
        pkg = _make_addon_package(
            name="Standard Pack", price=119000, message_count=150, tier="pro", validity_days=30
        )
        db_session.add(pkg)
        await db_session.commit()

        resp = await client.get("/api/chat/addons", headers=auth_headers)
        assert resp.status_code == 200
        items = resp.json()["data"]
        match = next((p for p in items if p["name"] == "Standard Pack"), None)
        assert match is not None
        assert match["message_count"] == 150
        assert match["tier"] == "pro"
        assert match["validity_days"] == 30
        assert match["price"] == 119000

    async def test_list_addons_empty_when_no_addon_packages(
        self, client, auth_headers, db_session: AsyncSession
    ):
        """No chat_addon rows → empty list, not error."""
        pdf = _make_pdf_package()
        db_session.add(pdf)
        await db_session.commit()

        resp = await client.get("/api/chat/addons", headers=auth_headers)
        assert resp.status_code == 200
        # Only chat_addon packages returned — "PDF Only" must be absent
        data = resp.json()["data"]
        assert not any(p["name"] == "PDF Only" for p in data)

    async def test_list_addons_requires_auth(self, client):
        """Unauthenticated → 401."""
        resp = await client.get("/api/chat/addons")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/chat/addons/{id}/purchase
# ---------------------------------------------------------------------------


class TestPurchaseAddonPackage:
    async def test_purchase_creates_pending_payment(
        self, client, auth_headers, db_session: AsyncSession
    ):
        """Happy path — creates UserPayment with status=1."""
        pkg = _make_addon_package(name="Purchase Test Pack")
        db_session.add(pkg)
        await db_session.commit()

        resp = await client.post(
            f"/api/chat/addons/{pkg.id}/purchase",
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["status"] == 1  # pending
        assert data["package_id"] == pkg.id
        assert data["price"] == pkg.price

    async def test_purchase_returns_bank_info(
        self, client, auth_headers, db_session: AsyncSession
    ):
        """Response includes bank fields (may be empty strings in test env)."""
        pkg = _make_addon_package(name="Bank Info Pack")
        db_session.add(pkg)
        await db_session.commit()

        resp = await client.post(
            f"/api/chat/addons/{pkg.id}/purchase",
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert "bank_account_number" in data
        assert "bank_account_holder" in data
        assert "payment_id" in data
        assert isinstance(data["payment_id"], int)

    async def test_purchase_404_on_unknown_package(self, client, auth_headers):
        """Non-existent package_id → 404."""
        resp = await client.post(
            "/api/chat/addons/999999/purchase",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_purchase_400_on_wrong_kind(
        self, client, auth_headers, db_session: AsyncSession
    ):
        """pdf_download package → 400 (not a chat add-on)."""
        pdf_pkg = _make_pdf_package(name="PDF For Purchase Test")
        db_session.add(pdf_pkg)
        await db_session.commit()

        resp = await client.post(
            f"/api/chat/addons/{pdf_pkg.id}/purchase",
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "not a chat add-on" in resp.json()["detail"].lower()

    async def test_purchase_requires_auth(self, client, db_session: AsyncSession):
        """No token → 401."""
        pkg = _make_addon_package(name="Auth Test Pack")
        db_session.add(pkg)
        await db_session.commit()

        resp = await client.post(f"/api/chat/addons/{pkg.id}/purchase")
        assert resp.status_code == 401
