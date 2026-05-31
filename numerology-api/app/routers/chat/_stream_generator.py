# ruff: noqa: UP045
"""SSE event generator for the streaming chat turn.

Extracted from messages.py to keep that router under 200 LOC.
Called by stream_message; top-level so it is directly importable and testable.

Pipeline (steps 3-9, steps 1-2 handled in messages.py before generator starts):
  3. Retrieval
  4. Prompt build
  5. Semantic cache lookup → hit: yield cached answer, decrement, done
  6. Prompt cache lookup / maybe_create → gemini_cache_id
  7. LLM streaming with optional cached_content
  8. Semantic cache insert (fire-and-forget)
  9. Persist assistant + decrement quota + commit → emit citations + done
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.chat.message import ChatMessage
from app.schemas.chat.message import MessageIn
from app.services.chat.chat_turn import (
    build_turn_prompt,
    persist_assistant_message,
    persist_no_info_assistant,
    run_retrieval,
)
from app.services.chat.citation_parser import build_citations
from app.services.chat.embedding_service import EmbeddingService
from app.services.chat.llm_service import LlmError, LlmService, StreamResult
from app.services.chat.prompt_cache_service import PromptCacheService
from app.services.chat.quota_service import QuotaConflictError, QuotaDecision, QuotaService
from app.services.chat.semantic_cache_service import SemanticCacheService
from app.services.chat.sse_formatter import sse_event

logger = logging.getLogger(__name__)

# Canonical "no info" fallback — must match system prompt rule #2.
NO_INFO_VI = "Tôi không có đủ thông tin để trả lời câu hỏi này."


async def _stream_cached_answer(
    answer: str, chunk_size: int = 40, delay: float = 0.02
):
    """Yield cached answer in fixed-size chunks with small delays for streaming UX (H7 fix)."""
    for i in range(0, len(answer), chunk_size):
        yield answer[i : i + chunk_size]
        await asyncio.sleep(delay)


async def generate_sse_events(  # noqa: C901
    db: AsyncSession,
    conv,
    user_msg: ChatMessage,
    body: MessageIn,
    llm: LlmService,
    decision: QuotaDecision,
    quota: Optional[QuotaService] = None,
    user_id: Optional[int] = None,
) -> AsyncIterator[bytes]:
    """Yield SSE byte frames for the full streaming chat turn (steps 3-9).

    CancelledError is re-raised before the generic except so FastAPI can handle
    client disconnects cleanly without logging a spurious 'stream_message failed'
    stacktrace.
    """
    conversation_id = conv.id
    tier = decision.tier or "flash"
    accumulated = ""

    try:
        # Step 3: retrieval
        pdf_id = body.pdf_context_id if body.pdf_context_id is not None else conv.pdf_context_id
        chunks, retrieval_ok = await run_retrieval(db, body.content, pdf_id)
        if not retrieval_ok:
            yield sse_event("delta", {"token": NO_INFO_VI})
            asst = await persist_no_info_assistant(db, conversation_id, NO_INFO_VI)
            await db.commit()
            yield sse_event(
                "done",
                {
                    "message_id": asst.id,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "model_used": None,
                },
            )
            return

        # Step 4: build prompt (A/B variant via user_id; falls back to canonical key)
        prompt = await build_turn_prompt(
            db, conversation_id, user_msg.id, body.content, chunks, user_id=user_id,
        )

        # Step 5: semantic cache lookup
        embedding_svc = EmbeddingService()
        semantic_cache = SemanticCacheService(db, embedding_svc)
        cached = await semantic_cache.lookup(body.content, tier)
        if cached is not None:
            await semantic_cache.increment_hit(cached.id)
            # Stream cached answer in chunks to simulate typewriter feel (H7 fix).
            async for chunk in _stream_cached_answer(cached.answer):
                yield sse_event("delta", {"token": chunk})
            # Persist assistant message for history consistency
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
            _quota_svc = quota if quota is not None else QuotaService(db)
            try:
                await _quota_svc.decrement(conv.user_id, decision)
            except QuotaConflictError:
                logger.warning("quota_conflict on cache hit conv=%s", conversation_id)
            await db.commit()
            yield sse_event("citations", {"citations": [c.model_dump() for c in cache_citations]})
            yield sse_event(
                "done",
                {
                    "message_id": asst_msg.id,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "model_used": "cache",
                    "from_cache": True,
                },
            )
            return

        # Step 6: prompt cache lookup / maybe_create
        pc_svc = PromptCacheService(db=db, client_provider=lambda: llm.client)
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

        # Step 7: stream tokens
        stream_result = StreamResult()
        async for token in llm.generate_stream(
            prompt.system,
            prompt.user_content,
            tier=tier,
            result=stream_result,
            cached_content=gemini_cache_id,
        ):
            accumulated += token
            yield sse_event("delta", {"token": token})

        if not accumulated:
            raise LlmError("LLM returned empty stream response")

        # Step 6b: parse citations
        citations = build_citations(accumulated, chunks)

        # Step 9: persist assistant message + quota — commit BEFORE cache insert (M5 fix).
        asst_msg = await persist_assistant_message(
            db,
            conversation_id,
            text=accumulated,
            model_used=stream_result.model_used or llm.model_id(tier),
            input_tokens=stream_result.input_tokens,
            output_tokens=stream_result.output_tokens,
            citations=citations,
        )

        # Decrement BEFORE commit so both assistant_message + quota change are atomic.
        quota_conflict = False
        _quota_svc = quota if quota is not None else QuotaService(db)
        try:
            await _quota_svc.decrement(conv.user_id, decision)
        except QuotaConflictError:
            quota_conflict = True
            logger.warning(
                "quota_conflict_post_stream conv=%s user=%s", conversation_id, conv.user_id
            )
        await db.commit()  # assistant message + quota committed — independent of cache insert

        # Step 8: semantic cache insert in own transaction (fire-and-forget).
        # Skip no-info canary to prevent caching stale responses permanently (M4 fix).
        if accumulated.strip() != NO_INFO_VI:
            try:
                await semantic_cache.insert(
                    body.content, tier, accumulated,
                    [c.model_dump() for c in citations],
                )
                await db.commit()
            except Exception:  # noqa: BLE001
                logger.warning(
                    "semantic_cache.insert failed for conv=%s (non-fatal)", conversation_id
                )
                await db.rollback()
        else:
            logger.info("skipping cache insert for no-info response in conv=%s", conversation_id)

        yield sse_event("citations", {"citations": [c.model_dump() for c in citations]})
        yield sse_event(
            "done",
            {
                "message_id": asst_msg.id,
                "input_tokens": stream_result.input_tokens,
                "output_tokens": stream_result.output_tokens,
                "model_used": asst_msg.model_used,
            },
        )
        if quota_conflict:
            yield sse_event(
                "error",
                {
                    "code": "quota_exceeded_postcommit",
                    "message": "Quota cạn trong lúc gửi. Lượt tới có thể yêu cầu mua thêm.",
                },
            )

    except asyncio.CancelledError:
        raise
    except Exception as exc:  # noqa: BLE001
        code = "llm_error" if isinstance(exc, LlmError) else "internal_error"
        logger.exception("stream_message failed for conv=%s", conversation_id)
        yield sse_event("error", {"code": code, "message": str(exc)})
