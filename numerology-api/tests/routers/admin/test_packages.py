# ruff: noqa: UP017, I001
"""Tests for POST /admin/packages — PackageCreate Pydantic validator (C3 fix).

Validates that:
- chat_addon package without required fields → 422
- chat_addon with all required fields → 201
- pdf_download is unaffected by addon field requirements
"""

from __future__ import annotations

ADMIN_PACKAGES_URL = "/admin/packages"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _addon_payload(**overrides) -> dict:
    """Base valid chat_addon payload; override individual fields to test rejections."""
    base = {
        "name": "Test Addon",
        "price": 49000,
        "price_sale": 49000,
        "number_download": 0,
        "package_kind": "chat_addon",
        "message_count": 50,
        "tier": "pro",
        "validity_days": 30,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# chat_addon field validation (C3)
# ---------------------------------------------------------------------------


class TestChatAddonValidation:
    async def test_create_chat_addon_rejects_missing_message_count(
        self, client, superuser_headers
    ):
        """message_count=None when package_kind=chat_addon → 422."""
        payload = _addon_payload(message_count=None)
        resp = await client.post(ADMIN_PACKAGES_URL, json=payload, headers=superuser_headers)
        assert resp.status_code == 422

    async def test_create_chat_addon_rejects_zero_message_count(
        self, client, superuser_headers
    ):
        """message_count=0 → 422 (must be >=1)."""
        payload = _addon_payload(message_count=0)
        resp = await client.post(ADMIN_PACKAGES_URL, json=payload, headers=superuser_headers)
        assert resp.status_code == 422

    async def test_create_chat_addon_rejects_missing_tier(
        self, client, superuser_headers
    ):
        """tier=None when package_kind=chat_addon → 422."""
        payload = _addon_payload(tier=None)
        resp = await client.post(ADMIN_PACKAGES_URL, json=payload, headers=superuser_headers)
        assert resp.status_code == 422

    async def test_create_chat_addon_rejects_missing_validity_days(
        self, client, superuser_headers
    ):
        """validity_days=None when package_kind=chat_addon → 422."""
        payload = _addon_payload(validity_days=None)
        resp = await client.post(ADMIN_PACKAGES_URL, json=payload, headers=superuser_headers)
        assert resp.status_code == 422

    async def test_create_chat_addon_rejects_zero_validity_days(
        self, client, superuser_headers
    ):
        """validity_days=0 → 422 (must be >=1)."""
        payload = _addon_payload(validity_days=0)
        resp = await client.post(ADMIN_PACKAGES_URL, json=payload, headers=superuser_headers)
        assert resp.status_code == 422

    async def test_create_chat_addon_happy_path(self, client, superuser_headers):
        """All required fields present → 201 with correct shape."""
        payload = _addon_payload(name="Happy Path Addon")
        resp = await client.post(ADMIN_PACKAGES_URL, json=payload, headers=superuser_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["package_kind"] == "chat_addon"
        assert data["message_count"] == 50
        assert data["tier"] == "pro"
        assert data["validity_days"] == 30

    async def test_create_pdf_download_does_not_require_addon_fields(
        self, client, superuser_headers
    ):
        """pdf_download package without addon fields → 201 (fields not required)."""
        payload = {
            "name": "PDF Pack",
            "price": 99000,
            "price_sale": 99000,
            "number_download": 5,
            "package_kind": "pdf_download",
        }
        resp = await client.post(ADMIN_PACKAGES_URL, json=payload, headers=superuser_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["package_kind"] == "pdf_download"
        assert data["message_count"] is None
        assert data["tier"] is None
        assert data["validity_days"] is None
