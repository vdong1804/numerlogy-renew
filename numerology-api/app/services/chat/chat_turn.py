"""Shared chat-turn helpers used by both the sync and streaming message endpoints.

Extracted here when messages.py would have exceeded 200 LOC after adding the
stream endpoint. Keeps routers thin and the core turn logic DRY.
"""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models.chat.message import ChatMessage
from app.schemas.chat.retrieval import RetrievedChunk
from app.services.chat.conversation_service import ConversationService
from app.services.chat.embedding_service import EmbeddingService
from app.services.chat.ab_test_service import AbTestService
from app.services.chat.prompt_builder import BuiltPrompt, build_prompt
from app.services.chat.prompt_settings_service import (
    KEY_SYSTEM_PROMPT,
    PromptSettingsService,
)
from app.services.chat.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)


async def persist_user_message(db: AsyncSession, conversation_id: int, content: str) -> ChatMessage:
    """Insert + commit user message. Commits immediately so the DB conn is
    freed before the (potentially long) LLM call."""
    msg = ChatMessage(
        conversation_id=conversation_id,
        role="user",
        content=content,
        tier="free",
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def run_retrieval(
    db: AsyncSession,
    query: str,
    pdf_context_id: int | None,
) -> tuple[list[RetrievedChunk], bool]:
    """Run KB/PDF retrieval.  Returns (chunks, ok) — ok=False on any exception."""
    embeddings = EmbeddingService()
    retrieval = RetrievalService(db, embeddings)
    try:
        chunks = await retrieval.retrieve(
            query,
            top_k=settings.rag_top_k_free,
            threshold=settings.rag_sim_threshold,
            pdf_context_id=pdf_context_id,
        )
        return chunks, True
    except Exception:  # noqa: BLE001
        logger.exception("retrieval failed")
        return [], False


async def build_turn_prompt(
    db: AsyncSession,
    conversation_id: int,
    user_msg_id: int,
    user_message: str,
    chunks: list[RetrievedChunk],
    user_id: int | None = None,
) -> BuiltPrompt:
    """Fetch recent history + admin prompt override and build prompt.

    The admin override is fetched via the in-process 60s cache, so the hot
    chat path stays free of an extra DB hit after the first lookup per
    process. When no override row exists the in-code SYSTEM_PROMPT is used.

    Phase 08: when `user_id` is provided, the A/B test variant is resolved
    and we look for a variant-specific override key
    (`chat_system_prompt_variant_a` / `_variant_b`). Falls back to the
    canonical key, then to the in-code constant.
    """
    conv_svc = ConversationService(db)
    history = await conv_svc.get_recent_messages(
        conversation_id, limit=settings.history_max_messages + 1
    )
    history = [m for m in history if m.id != user_msg_id]
    prompt_settings = PromptSettingsService(db)
    override = await _resolve_prompt_override(db, prompt_settings, user_id)
    return build_prompt(
        user_message,
        chunks,
        history=history,
        system_prompt_override=override,
    )


async def _resolve_prompt_override(
    db: AsyncSession,
    prompt_settings: PromptSettingsService,
    user_id: int | None,
) -> str | None:
    """Variant-aware override lookup with fall-through to the canonical key."""
    if user_id is None:
        return await prompt_settings.get_override(KEY_SYSTEM_PROMPT)
    variant = await AbTestService(db).get_or_assign_variant(user_id)
    if variant != "control":
        variant_key = f"{KEY_SYSTEM_PROMPT}_{variant}"
        variant_override = await prompt_settings.get_override(variant_key)
        if variant_override is not None and variant_override.strip():
            return variant_override
    return await prompt_settings.get_override(KEY_SYSTEM_PROMPT)


async def persist_no_info_assistant(
    db: AsyncSession, conversation_id: int, text: str
) -> ChatMessage:
    """Insert + flush a canonical no-info assistant row (caller owns commit).

    Used by both the sync path (_persist_and_return_canonical) and the stream
    path (no-info branch) so the row creation logic stays in one place.
    """
    msg = ChatMessage(
        conversation_id=conversation_id,
        role="assistant",
        content=text,
        tier="free",
    )
    db.add(msg)
    await db.flush()
    await db.refresh(msg)
    return msg


async def persist_assistant_message(
    db: AsyncSession,
    conversation_id: int,
    text: str,
    model_used: str | None,
    input_tokens: int,
    output_tokens: int,
    citations: list,
) -> ChatMessage:
    """Insert + flush assistant message (caller owns commit/rollback)."""
    msg = ChatMessage(
        conversation_id=conversation_id,
        role="assistant",
        content=text,
        model_used=model_used,
        tier="free",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        citations=[c.model_dump() for c in citations],
    )
    db.add(msg)
    await db.flush()
    await db.refresh(msg)
    return msg
