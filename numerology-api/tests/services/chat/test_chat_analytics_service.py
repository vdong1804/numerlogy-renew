"""Unit tests for ChatAnalyticsService — seeded conversations + messages."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.db.models.chat.conversation import ChatConversation
from app.db.models.chat.message import ChatMessage
from app.services.chat.chat_analytics_service import ChatAnalyticsService, default_window


def _seed_conversation(db, user_id: int, when: datetime) -> ChatConversation:
    conv = ChatConversation(
        user_id=user_id,
        title="seed",
        created_at=when,
        updated_at=when,
    )
    db.add(conv)
    return conv


def _seed_message(
    db, conv_id: int, role: str, tier: str, model: str | None,
    input_tokens: int, output_tokens: int, when: datetime,
    content: str = "hello",
) -> ChatMessage:
    msg = ChatMessage(
        conversation_id=conv_id,
        role=role,
        content=content,
        tier=tier,
        model_used=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        created_at=when,
    )
    db.add(msg)
    return msg


@pytest.mark.asyncio
async def test_overview_counts_and_users(db_session, user, superuser):
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    today = now

    c1 = _seed_conversation(db_session, user.id, yesterday)
    c2 = _seed_conversation(db_session, superuser.id, today)
    await db_session.flush()

    # 3 messages yesterday (free), 2 today (paid)
    _seed_message(db_session, c1.id, "user", "free", None, 0, 0, yesterday, "Câu hỏi A")
    _seed_message(
        db_session, c1.id, "assistant", "free", "gemini-2.0-flash", 100, 50, yesterday
    )
    _seed_message(db_session, c1.id, "user", "free", None, 0, 0, yesterday, "Câu hỏi A")
    _seed_message(db_session, c2.id, "user", "paid", None, 0, 0, today, "Câu hỏi B")
    _seed_message(
        db_session, c2.id, "assistant", "paid", "gemini-2.0-pro", 200, 80, today
    )
    await db_session.flush()

    svc = ChatAnalyticsService(db_session)
    start, end = default_window(7)
    overview = await svc.overview(start, end)

    assert overview.total_messages == 5
    assert overview.total_conversations == 2
    assert overview.unique_users == 2


@pytest.mark.asyncio
async def test_top_questions_groups_by_content(db_session, user):
    now = datetime.now(timezone.utc)
    conv = _seed_conversation(db_session, user.id, now)
    await db_session.flush()

    _seed_message(db_session, conv.id, "user", "free", None, 0, 0, now, "Số mệnh 8")
    _seed_message(db_session, conv.id, "user", "free", None, 0, 0, now, "Số mệnh 8")
    _seed_message(db_session, conv.id, "user", "free", None, 0, 0, now, "Số mệnh 8")
    _seed_message(db_session, conv.id, "user", "free", None, 0, 0, now, "Số mệnh 5")
    _seed_message(
        db_session, conv.id, "assistant", "free", "gemini-2.0-flash", 50, 30, now
    )  # excluded — not user role
    await db_session.flush()

    svc = ChatAnalyticsService(db_session)
    start, end = default_window(7)
    overview = await svc.overview(start, end)

    questions = {q.question: q.count for q in overview.top_questions}
    assert questions["Số mệnh 8"] == 3
    assert questions["Số mệnh 5"] == 1
    # Assistant content excluded
    assert "hello" not in questions


@pytest.mark.asyncio
async def test_cost_breakdown_uses_pricing(db_session, user):
    now = datetime.now(timezone.utc)
    conv = _seed_conversation(db_session, user.id, now)
    await db_session.flush()

    # Flash: 1M input + 1M output → $0.10 + $0.40 = $0.50
    _seed_message(
        db_session, conv.id, "assistant", "free", "gemini-2.0-flash",
        1_000_000, 1_000_000, now,
    )
    await db_session.flush()

    svc = ChatAnalyticsService(db_session)
    start, end = default_window(7)
    overview = await svc.overview(start, end)

    flash_rows = [c for c in overview.cost_by_model if c.model == "gemini-2.0-flash"]
    assert len(flash_rows) == 1
    assert flash_rows[0].input_tokens == 1_000_000
    assert flash_rows[0].output_tokens == 1_000_000
    assert flash_rows[0].estimated_usd == pytest.approx(0.50, rel=1e-3)


@pytest.mark.asyncio
async def test_overview_empty_window(db_session):
    svc = ChatAnalyticsService(db_session)
    start, end = default_window(7)
    overview = await svc.overview(start, end)
    assert overview.total_messages == 0
    assert overview.unique_users == 0
    assert overview.estimated_total_cost_usd == 0.0
    assert overview.semantic_cache_hit_rate == 0.0
