# ruff: noqa: UP045, UP017
"""Message endpoints — POST send_message (sync) + POST stream_message (SSE).

Pipeline (both endpoints identical):
  1. Auth (dep) → conv ownership check → user_msg commit
  2. Rate limit: peek_tier (cheap) → check_and_consume(user_id, ip, tier)  [per spec]
  3. Quota gate: full check() → 402 if can_send=False
  4. Retrieval: top-k KB/PDF chunks
  5. Semantic cache lookup → hit: skip LLM, decrement, return from_cache=True
  6. Prompt cache: get_live_handle or maybe_create → gemini_cache_id
  7. LLM call with optional cached_content
  8. Post-LLM: semantic_cache.insert (fire-and-forget, own transaction)
  9. Persist assistant message + decrement quota + commit
"""

from __future__ import annotations

import logging
import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.deps import get_current_user, get_db
from app.routers.chat._hardening_gate import run_hardening_gates
from app.routers.chat._stream_generator import NO_INFO_VI, generate_sse_events
from app.schemas.chat.message import MessageIn, MessageOut
from app.services.chat.chat_turn import (
    build_turn_prompt,
    persist_assistant_message,
    persist_no_info_assistant,
    persist_user_message,
    run_retrieval,
)
from app.services.chat.citation_parser import build_citations
from app.services.chat.conversation_service import ConversationService
from app.services.chat.embedding_service import EmbeddingService
from app.services.chat.llm_service import LlmError, LlmService
from app.services.chat.prompt_cache_service import PromptCacheService
from app.services.chat.quota_service import QuotaConflictError, QuotaDecision, QuotaService
from app.services.chat.rate_limit_service import RateLimitService
from app.services.chat.semantic_cache_service import SemanticCacheService
from app.utils.network import get_client_ip

logger = logging.getLogger(__name__)

messages_router = APIRouter(prefix="/api/chat/conversations", tags=["chat"])

# SSE response headers for Nginx pass-through (disable buffering).
_SSE_HEADERS = {
    "X-Accel-Buffering": "no",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
}


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


async def _check_quota_or_402(db: AsyncSession, user_id: int) -> QuotaDecision:
    """Run quota check; raise HTTP 402 immediately if quota exhausted."""
    decision = await QuotaService(db).check(user_id)
    if not decision.can_send:
        raise HTTPException(
            status_code=402,
            detail={"code": "quota_exceeded", "upsell": True},
        )
    return decision


async def _check_rate_limit_or_429(
    db: AsyncSession, user_id: int, ip: str, tier: str
) -> None:
    """Check rate limit; raise HTTP 429 with Retry-After if limited."""
    result = await RateLimitService(db).check_and_consume(
        user_id=user_id, ip=ip, tier=tier
    )
    if not result.allowed:
        retry_after = math.ceil(result.retry_after)
        # Phase 08: record rate-limit hit for cost dashboard.
        try:
            from app.services.chat.cost_monitor_service import CostMonitorService
            await CostMonitorService(db).increment_rate_limit_hit()
            await db.commit()
        except Exception:  # noqa: BLE001
            logger.warning("cost_monitor.increment_rate_limit_hit failed", exc_info=True)
            await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "rate_limited",
                "retry_after": retry_after,
                "reason": result.reason,
                "message": f"Bạn gửi tin nhắn quá nhanh. Vui lòng đợi {retry_after} giây.",
            },
            headers={"Retry-After": str(retry_after)},
        )


async def _persist_and_return_canonical(
    db: AsyncSession, conversation_id: int, text: str
) -> dict:
    """Save a canonical assistant reply (no LLM call) and return MessageOut envelope."""
    asst = await persist_no_info_assistant(db, conversation_id, text)
    out = MessageOut(
        id=asst.id,
        role=asst.role,
        content=asst.content,
        citations=[],
        model_used=None,
        tier=asst.tier,
        input_tokens=0,
        output_tokens=0,
        created_at=asst.created_at,
    )
    return {"data": out.model_dump(mode="json")}


def _build_prompt_cache_svc(db: AsyncSession, llm: LlmService) -> PromptCacheService:
    return PromptCacheService(db=db, client_provider=lambda: llm.client)


# ---------------------------------------------------------------------------
# GET list
# ---------------------------------------------------------------------------


@messages_router.get("/{conversation_id}/messages", response_model=dict)
async def list_messages(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = ConversationService(db)
    items = await svc.list_messages(conversation_id, user.id)
    return {"data": [MessageOut.model_validate(m).model_dump(mode="json") for m in items]}


# ---------------------------------------------------------------------------
# POST — sync (non-streaming)
# ---------------------------------------------------------------------------


@messages_router.post(
    "/{conversation_id}/messages",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    conversation_id: int,
    body: MessageIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Full chat turn — see module docstring for the pipeline."""
    conv_svc = ConversationService(db)
    conv = await conv_svc.get_owned(conversation_id, user.id)  # step 1

    # Phase 08 hardening gates BEFORE persisting the user message so a
    # disabled flag / abuse block / missing CAPTCHA cannot pollute history.
    ip = get_client_ip(request)
    await run_hardening_gates(db, user, body.content, body.captcha_token, ip)

    user_msg = await persist_user_message(db, conversation_id, body.content)  # step 1b

    # Step 2: rate limit first (per spec), using cheap tier peek to avoid full quota query.
    # Step 3: full quota check — raises 402 if exhausted.
    tier_for_rl = await QuotaService(db).peek_tier(user.id)  # cheap read, no decrement
    await _check_rate_limit_or_429(db, user.id, ip, tier_for_rl)  # step 2
    decision = await _check_quota_or_402(db, user.id)  # step 3 gate
    tier = decision.tier or "flash"

    # body.pdf_context_id overrides the conversation-level attachment when provided.
    pdf_id = body.pdf_context_id if body.pdf_context_id is not None else conv.pdf_context_id
    chunks, retrieval_ok = await run_retrieval(db, body.content, pdf_id)  # step 4
    if not retrieval_ok:
        return await _persist_and_return_canonical(db, conversation_id, NO_INFO_VI)

    # Step 5: semantic cache lookup
    embedding_svc = EmbeddingService()
    semantic_cache = SemanticCacheService(db, embedding_svc)
    cached = await semantic_cache.lookup(body.content, tier)
    if cached is not None:
        await semantic_cache.increment_hit(cached.id)
        # Persist assistant message with model_used="cache" for history consistency
        cache_citations = build_citations(cached.answer, chunks)
        asst_msg = await persist_assistant_message(
            db,
            conversation_id,
            text=cached.answer,
            model_used="cache",
            input_tokens=0,
            output_tokens=0,
            citations=cache_citations,
        )
        try:
            await QuotaService(db).decrement(user.id, decision)
        except QuotaConflictError:
            logger.warning("QuotaConflictError on cache hit for user=%s", user.id)
        out = MessageOut(
            id=asst_msg.id,
            role=asst_msg.role,
            content=asst_msg.content,
            citations=cache_citations,
            model_used="cache",
            tier=asst_msg.tier,
            input_tokens=0,
            output_tokens=0,
            created_at=asst_msg.created_at,
            from_cache=True,
        )
        return {"data": out.model_dump(mode="json")}

    # Step 4b: build prompt (A/B variant resolved inside via user_id).
    prompt = await build_turn_prompt(
        db, conversation_id, user_msg.id, body.content, chunks, user_id=user.id,
    )

    # Step 6: prompt cache
    llm = LlmService()
    pc_svc = _build_prompt_cache_svc(db, llm)
    cache_key = PromptCacheService.compute_key(
        prompt.system, [c.chunk_id for c in chunks], tier
    )
    pc_result = await pc_svc.get_live_handle(cache_key)
    gemini_cache_id: Optional[str] = None
    if pc_result is not None:
        gemini_cache_id = pc_result.gemini_cache_id
    else:
        maybe = await pc_svc.maybe_create(
            cache_key=cache_key,
            system=prompt.system,
            kb_chunks=[{"content": c.content, "title": c.title or ""} for c in chunks],
            tier=tier,
            model=llm.model_id(tier),
        )
        if maybe is not None:
            gemini_cache_id = maybe.gemini_cache_id

    # Step 7: LLM call
    try:
        resp = await llm.generate(
            prompt.system,
            prompt.user_content,
            tier=tier,
            cached_content=gemini_cache_id,
        )
    except LlmError as exc:
        logger.exception("LLM call failed for conv=%s", conversation_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Vui lòng thử lại sau giây lát.",
        ) from exc

    citations = build_citations(resp.text, chunks)  # step 6b

    # Step 9: persist assistant message + quota decrement.
    # Commit first so a cache-insert failure cannot roll back the assistant message (M5 fix).
    asst_msg = await persist_assistant_message(
        db,
        conversation_id,
        text=resp.text,
        model_used=resp.model_used,
        input_tokens=resp.input_tokens,
        output_tokens=resp.output_tokens,
        citations=citations,
    )
    try:
        await QuotaService(db).decrement(user.id, decision)
    except QuotaConflictError:
        logger.warning("QuotaConflictError after send for user=%s (race, ignoring)", user.id)
    await db.commit()  # commit assistant message + quota — independent of cache insert

    # Step 8: semantic cache insert in own transaction (fire-and-forget).
    # Skip no-info canary to prevent permanently caching stale "no info" responses (M4 fix).
    if resp.text.strip() != NO_INFO_VI:
        try:
            await semantic_cache.insert(
                body.content, tier, resp.text,
                [c.model_dump() for c in citations],
            )
            await db.commit()
        except Exception:  # noqa: BLE001
            logger.warning("semantic_cache.insert failed for conv=%s (non-fatal)", conversation_id)
            await db.rollback()
    else:
        logger.info("skipping cache insert for no-info response in conv=%s", conversation_id)

    out = MessageOut(
        id=asst_msg.id,
        role=asst_msg.role,
        content=asst_msg.content,
        citations=citations,
        model_used=asst_msg.model_used,
        tier=asst_msg.tier,
        input_tokens=asst_msg.input_tokens,
        output_tokens=asst_msg.output_tokens,
        created_at=asst_msg.created_at,
    )
    return {"data": out.model_dump(mode="json")}


# ---------------------------------------------------------------------------
# POST — SSE streaming
# ---------------------------------------------------------------------------


@messages_router.post("/{conversation_id}/messages/stream")
async def stream_message(
    conversation_id: int,
    body: MessageIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """SSE streaming chat turn — same pipeline, tokens yielded incrementally.

    Event schema:
        event: delta    data: {"token": "<text chunk>"}
        event: citations data: {"citations": [...]}
        event: done     data: {"message_id": N, "input_tokens": N,
                               "output_tokens": N, "model_used": "..."}
        event: error    data: {"code": "...", "message": "...",
                                "retry_after": N}  # only for rate_limited
    """
    conv_svc = ConversationService(db)
    conv = await conv_svc.get_owned(conversation_id, user.id)  # 404 before stream opens

    # Phase 08 hardening gates — must run pre-persist (see send_message rationale).
    ip = get_client_ip(request)
    await run_hardening_gates(db, user, body.content, body.captcha_token, ip)

    user_msg = await persist_user_message(db, conversation_id, body.content)

    # Rate limit first (per spec), then quota check — both before StreamingResponse is built.
    tier_for_rl = await QuotaService(db).peek_tier(user.id)  # cheap read, no decrement
    await _check_rate_limit_or_429(db, user.id, ip, tier_for_rl)  # step 2
    decision = await _check_quota_or_402(db, user.id)  # step 3
    # tier is extracted from decision inside generate_sse_events

    llm = LlmService()
    quota_svc = QuotaService(db)
    return StreamingResponse(
        generate_sse_events(
            db, conv, user_msg, body, llm, decision, quota=quota_svc, user_id=user.id,
        ),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )
