"""Integration tests for POST/PATCH/DELETE /api/chat/conversations/{id}/pdf-context.

UserPdfService.ingest is monkeypatched so tests don't touch the real Gemini API
or pypdf parsing.
"""

import io

import pytest
from sqlalchemy import select

from app.db.models.chat.user_pdf_index import UserPdfIndex
from app.services.chat.user_pdf_service import PdfIngestResult, UserPdfService


@pytest.fixture
def patch_ingest(monkeypatch):
    """Return a UserPdfIngest stub that creates a UserPdfIndex row and returns it."""
    from datetime import datetime, timedelta, timezone

    async def _stub_ingest(self, user_id, pdf_bytes, filename=None):
        # Persist a real UserPdfIndex so the router's auto-attach has a valid id
        idx = UserPdfIndex(
            user_id=user_id,
            pdf_hash="a" * 64,
            filename=filename,
            page_count=2,
            parsed_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        self.session.add(idx)
        await self.session.flush()
        await self.session.refresh(idx)
        return PdfIngestResult(
            pdf_index=idx,
            chunks_created=4,
            matched=False,
            matched_report_id=None,
            reused_existing=False,
        )

    monkeypatch.setattr(UserPdfService, "ingest", _stub_ingest)


async def _make_conv(client, headers) -> int:
    resp = await client.post(
        "/api/chat/conversations", json={"title": "pdf-tests"}, headers=headers
    )
    return resp.json()["data"]["id"]


class TestUploadPdf:
    async def test_upload_happy_path_attaches_to_conversation(
        self, client, auth_headers, db_session, patch_ingest
    ):
        conv_id = await _make_conv(client, auth_headers)
        files = {"file": ("r.pdf", io.BytesIO(b"%PDF-1.4 dummy"), "application/pdf")}
        resp = await client.post(
            f"/api/chat/conversations/{conv_id}/upload-pdf",
            headers=auth_headers,
            files=files,
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["pdf_context_id"] > 0
        assert data["matched"] is False
        assert data["chunks_created"] == 4

    async def test_upload_non_pdf_returns_415(
        self, client, auth_headers, patch_ingest
    ):
        conv_id = await _make_conv(client, auth_headers)
        files = {"file": ("r.pdf", io.BytesIO(b"not a pdf"), "application/pdf")}
        resp = await client.post(
            f"/api/chat/conversations/{conv_id}/upload-pdf",
            headers=auth_headers,
            files=files,
        )
        assert resp.status_code == 415

    async def test_upload_oversize_returns_413(
        self, client, auth_headers, patch_ingest
    ):
        conv_id = await _make_conv(client, auth_headers)
        big = b"%PDF-1.4" + b"x" * (26 * 1024 * 1024)
        files = {"file": ("big.pdf", io.BytesIO(big), "application/pdf")}
        resp = await client.post(
            f"/api/chat/conversations/{conv_id}/upload-pdf",
            headers=auth_headers,
            files=files,
        )
        assert resp.status_code == 413

    async def test_upload_other_users_conversation_returns_404(
        self, client, auth_headers, superuser_headers, patch_ingest
    ):
        conv_id = await _make_conv(client, superuser_headers)
        files = {"file": ("r.pdf", io.BytesIO(b"%PDF-1.4 x"), "application/pdf")}
        resp = await client.post(
            f"/api/chat/conversations/{conv_id}/upload-pdf",
            headers=auth_headers,
            files=files,
        )
        assert resp.status_code == 404

    async def test_upload_unauthenticated_returns_401(self, client):
        files = {"file": ("r.pdf", io.BytesIO(b"%PDF-1.4 x"), "application/pdf")}
        resp = await client.post(
            "/api/chat/conversations/1/upload-pdf", files=files
        )
        assert resp.status_code == 401


class TestPatchPdfContext:
    async def test_patch_clears_attachment(
        self, client, auth_headers, patch_ingest
    ):
        conv_id = await _make_conv(client, auth_headers)
        # First attach via upload
        files = {"file": ("r.pdf", io.BytesIO(b"%PDF-1.4 x"), "application/pdf")}
        await client.post(
            f"/api/chat/conversations/{conv_id}/upload-pdf",
            headers=auth_headers,
            files=files,
        )
        # Now clear
        resp = await client.patch(
            f"/api/chat/conversations/{conv_id}/pdf-context",
            json={"pdf_context_id": None},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["pdf_context_id"] is None

    async def test_patch_unknown_pdf_context_id_returns_404(
        self, client, auth_headers
    ):
        conv_id = await _make_conv(client, auth_headers)
        resp = await client.patch(
            f"/api/chat/conversations/{conv_id}/pdf-context",
            json={"pdf_context_id": 99999},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_patch_other_users_pdf_returns_404(
        self, client, auth_headers, superuser_headers, db_session, patch_ingest
    ):
        # superuser uploads a PDF
        super_conv = await _make_conv(client, superuser_headers)
        files = {"file": ("r.pdf", io.BytesIO(b"%PDF-1.4 x"), "application/pdf")}
        super_resp = await client.post(
            f"/api/chat/conversations/{super_conv}/upload-pdf",
            headers=superuser_headers,
            files=files,
        )
        super_pdf_id = super_resp.json()["data"]["pdf_context_id"]

        # regular user tries to attach the other user's pdf_context_id
        my_conv = await _make_conv(client, auth_headers)
        resp = await client.patch(
            f"/api/chat/conversations/{my_conv}/pdf-context",
            json={"pdf_context_id": super_pdf_id},
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestDeletePdfContext:
    async def test_delete_clears_attachment(
        self, client, auth_headers, patch_ingest
    ):
        conv_id = await _make_conv(client, auth_headers)
        files = {"file": ("r.pdf", io.BytesIO(b"%PDF-1.4 x"), "application/pdf")}
        await client.post(
            f"/api/chat/conversations/{conv_id}/upload-pdf",
            headers=auth_headers,
            files=files,
        )
        resp = await client.delete(
            f"/api/chat/conversations/{conv_id}/pdf-context",
            headers=auth_headers,
        )
        assert resp.status_code == 204

    async def test_delete_other_users_conv_returns_404(
        self, client, auth_headers, superuser_headers
    ):
        conv_id = await _make_conv(client, superuser_headers)
        resp = await client.delete(
            f"/api/chat/conversations/{conv_id}/pdf-context",
            headers=auth_headers,
        )
        assert resp.status_code == 404
