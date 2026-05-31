"""Unit tests for PdfMatchService — user-scoped SHA256 lookup."""

import pytest

from app.db.models.user_report import UserReport
from app.services.chat.pdf_match_service import PdfMatchService, sha256_hex


def test_sha256_hex_is_deterministic_and_64chars():
    h1 = sha256_hex(b"hello")
    h2 = sha256_hex(b"hello")
    assert h1 == h2
    assert len(h1) == 64


def test_sha256_hex_differs_for_different_input():
    assert sha256_hex(b"a") != sha256_hex(b"b")


async def _make_report(db, user_id: int, file_hash: str | None) -> UserReport:
    # product_id is a required FK — we just stub with 1; tests don't rely on its referential
    # integrity since the sqlite test setup uses Base.metadata.create_all without enforcing FKs.
    r = UserReport(
        user_id=user_id,
        product_id=1,
        pdf_path="/tmp/fake.pdf",
        file_hash=file_hash,
        input_payload={},
    )
    db.add(r)
    await db.flush()
    return r


@pytest.mark.asyncio
async def test_find_match_returns_report_when_hash_matches(db_session, user):
    h = sha256_hex(b"some pdf bytes")
    await _make_report(db_session, user.id, h)
    svc = PdfMatchService(db_session)
    found = await svc.find_match(h, user.id)
    assert found is not None
    assert found.user_id == user.id
    assert found.file_hash == h


@pytest.mark.asyncio
async def test_find_match_returns_none_when_no_match(db_session, user):
    svc = PdfMatchService(db_session)
    assert await svc.find_match("0" * 64, user.id) is None


@pytest.mark.asyncio
async def test_find_match_isolates_per_user(db_session, user, superuser):
    h = sha256_hex(b"shared content")
    # Other user owns a report with this hash
    await _make_report(db_session, superuser.id, h)
    svc = PdfMatchService(db_session)
    assert await svc.find_match(h, user.id) is None  # cannot see other user's report
    assert (await svc.find_match(h, superuser.id)) is not None


@pytest.mark.asyncio
async def test_find_match_empty_hash_returns_none(db_session, user):
    svc = PdfMatchService(db_session)
    assert await svc.find_match("", user.id) is None
