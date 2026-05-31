"""Integration tests for the admin chatbot router (Phase 07).

Covers superuser guard, KB upload/list/delete, prompt CRUD, addon grant.
EmbeddingService.embed_batch is monkeypatched to avoid Gemini calls.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.package import Package
from app.services.chat.embedding_service import EmbeddingService
from app.services.chat.prompt_settings_service import invalidate_cache

BASE = "/admin/chatbot"


@pytest.fixture(autouse=True)
def _patch_embeddings(monkeypatch):
    """All chat embed_batch calls return 768-dim zeros — fast + offline."""

    async def _fake(self, texts):
        return [[0.0] * 768 for _ in texts]

    monkeypatch.setattr(EmbeddingService, "embed_batch", _fake)
    invalidate_cache()
    yield
    invalidate_cache()


@pytest.fixture
async def addon_package(db_session: AsyncSession) -> Package:
    pkg = Package(
        name="Pack 50",
        price=49000,
        price_sale=49000,
        number_download=0,
        package_kind="chat_addon",
        message_count=50,
        tier="paid",
        validity_days=30,
    )
    db_session.add(pkg)
    await db_session.flush()
    await db_session.refresh(pkg)
    return pkg


# ---------------------------------------------------------------------------
# Auth guard
# ---------------------------------------------------------------------------


class TestAuthGuard:
    async def test_non_superuser_gets_403(self, client, auth_headers):
        resp = await client.get(f"{BASE}/prompt", headers=auth_headers)
        assert resp.status_code == 403

    async def test_unauthenticated_gets_401(self, client):
        resp = await client.get(f"{BASE}/prompt")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# KB upload + list + delete
# ---------------------------------------------------------------------------


class TestKbDocuments:
    async def test_upload_txt_creates_doc(self, client, superuser_headers):
        files = {"file": ("notes.txt", b"para one\n\npara two body", "text/plain")}
        resp = await client.post(
            f"{BASE}/kb/upload?title=Notes",
            files=files,
            headers=superuser_headers,
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["document"]["source_type"] == "admin_upload"
        assert body["document"]["title"] == "Notes"
        assert body["file_kind"] == "txt"
        assert body["chunks_created"] >= 1

    async def test_upload_unsupported_type_415(self, client, superuser_headers):
        files = {"file": ("evil.exe", b"\x00\x00", "application/octet-stream")}
        resp = await client.post(
            f"{BASE}/kb/upload", files=files, headers=superuser_headers
        )
        assert resp.status_code == 415

    async def test_upload_empty_422(self, client, superuser_headers):
        files = {"file": ("blank.txt", b"   ", "text/plain")}
        resp = await client.post(
            f"{BASE}/kb/upload", files=files, headers=superuser_headers
        )
        assert resp.status_code == 422

    async def test_list_and_delete_roundtrip(self, client, superuser_headers):
        # seed via upload
        files = {"file": ("a.txt", b"alpha alpha alpha", "text/plain")}
        up = await client.post(
            f"{BASE}/kb/upload", files=files, headers=superuser_headers
        )
        assert up.status_code == 201
        doc_id = up.json()["document"]["id"]

        listing = await client.get(
            f"{BASE}/kb/documents", headers=superuser_headers
        )
        assert listing.status_code == 200
        items = listing.json()["items"]
        assert any(d["id"] == doc_id for d in items)

        deleted = await client.delete(
            f"{BASE}/kb/documents/{doc_id}", headers=superuser_headers
        )
        assert deleted.status_code == 204

        listing2 = await client.get(
            f"{BASE}/kb/documents", headers=superuser_headers
        )
        assert all(d["id"] != doc_id for d in listing2.json()["items"])

    async def test_delete_unknown_404(self, client, superuser_headers):
        resp = await client.delete(
            f"{BASE}/kb/documents/999999", headers=superuser_headers
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Prompt CRUD
# ---------------------------------------------------------------------------


class TestPrompt:
    async def test_get_returns_default_when_no_override(self, client, superuser_headers):
        resp = await client.get(f"{BASE}/prompt", headers=superuser_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["is_override"] is False
        assert body["value"]  # default SYSTEM_PROMPT
        assert body["version"] is None

    async def test_put_then_get_returns_override(self, client, superuser_headers):
        put = await client.put(
            f"{BASE}/prompt",
            json={"value": "Custom rules"},
            headers=superuser_headers,
        )
        assert put.status_code == 200
        assert put.json()["version"] == 1

        got = await client.get(f"{BASE}/prompt", headers=superuser_headers)
        assert got.status_code == 200
        body = got.json()
        assert body["is_override"] is True
        assert body["value"] == "Custom rules"

    async def test_put_twice_bumps_version_and_writes_history(
        self, client, superuser_headers
    ):
        await client.put(
            f"{BASE}/prompt", json={"value": "v1"}, headers=superuser_headers
        )
        r2 = await client.put(
            f"{BASE}/prompt", json={"value": "v2"}, headers=superuser_headers
        )
        assert r2.json()["version"] == 2

        hist = await client.get(
            f"{BASE}/prompt/history", headers=superuser_headers
        )
        assert hist.status_code == 200
        # at least one snapshot (the v1 row captured when bumping to v2)
        assert len(hist.json()["items"]) >= 1

    async def test_delete_resets_to_default(self, client, superuser_headers):
        await client.put(
            f"{BASE}/prompt", json={"value": "override"}, headers=superuser_headers
        )
        d = await client.delete(f"{BASE}/prompt", headers=superuser_headers)
        assert d.status_code == 204

        got = await client.get(f"{BASE}/prompt", headers=superuser_headers)
        assert got.json()["is_override"] is False


# ---------------------------------------------------------------------------
# Analytics overview
# ---------------------------------------------------------------------------


class TestAnalyticsOverview:
    async def test_empty_overview(self, client, superuser_headers):
        resp = await client.get(
            f"{BASE}/analytics/overview?days=7", headers=superuser_headers
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_messages"] == 0
        assert body["semantic_cache_hit_rate"] == 0.0


# ---------------------------------------------------------------------------
# Manual addon grant
# ---------------------------------------------------------------------------


class TestGrantAddon:
    async def test_grant_creates_purchase(
        self, client, superuser_headers, user, addon_package
    ):
        resp = await client.post(
            f"{BASE}/users/{user.id}/grant-addon",
            json={"package_id": addon_package.id, "notes": "comp"},
            headers=superuser_headers,
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["user_id"] == user.id
        assert body["remaining_messages"] == addon_package.message_count
        # expiry should be in the future; SQLite drops tzinfo so normalise.
        raw = body["expires_at"]
        exp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        assert exp > datetime.now(timezone.utc)

    async def test_grant_rejects_non_addon_package(
        self, client, superuser_headers, user, db_session
    ):
        pkg = Package(
            name="PDF only",
            price=10000,
            price_sale=10000,
            number_download=1,
            package_kind="pdf_download",
        )
        db_session.add(pkg)
        await db_session.flush()
        await db_session.refresh(pkg)

        resp = await client.post(
            f"{BASE}/users/{user.id}/grant-addon",
            json={"package_id": pkg.id},
            headers=superuser_headers,
        )
        assert resp.status_code == 400

    async def test_grant_unknown_user(self, client, superuser_headers, addon_package):
        resp = await client.post(
            f"{BASE}/users/999999/grant-addon",
            json={"package_id": addon_package.id},
            headers=superuser_headers,
        )
        assert resp.status_code == 404
