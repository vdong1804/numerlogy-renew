# ruff: noqa: UP045, UP017
"""Phase 08 hardening gates for chat send paths.

Single async helper that runs the launch / abuse / CAPTCHA / prompt-injection
checks before we touch the LLM or quota tables. Raises HTTPException with the
canonical error codes so the router stays thin and stream + sync paths share
identical behaviour.

Order of checks (cheapest-first):
  1. Feature flag (`chatbot_public`) — 503 if disabled.
  2. User suspension (chat_suspended_at) — 403 if banned.
  3. Prompt injection (regex) — 400 + +5 abuse score.
  4. CAPTCHA required → verify Turnstile token; 401 if missing/invalid.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.services.chat.abuse_detection_service import (
    AbuseDetectionService,
    SCORE_PROMPT_INJECTION,
    is_prompt_injection,
)
from app.services.chat.feature_flag_service import FeatureFlagService
from app.services.turnstile_service import verify_chat_captcha

logger = logging.getLogger(__name__)


async def run_hardening_gates(
    db: AsyncSession,
    user: User,
    content: str,
    captcha_token: Optional[str],
    remote_ip: Optional[str],
) -> None:
    """Run all Phase-08 pre-LLM checks. Raises HTTPException on rejection."""
    # 1. Feature flag (master kill-switch + rollout %).
    flags = FeatureFlagService(db)
    if not await flags.is_enabled("chatbot_public", user.id):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "chatbot_disabled",
                "message": "Tính năng chatbot tạm thời không khả dụng.",
            },
        )

    # 2. Suspension (>= SUSPEND_THRESHOLD abuse score).
    if user.chat_suspended_at is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "chat_suspended",
                "message": "Tài khoản của bạn đã tạm khóa khỏi chatbot.",
            },
        )

    # 3. Prompt injection — block + log + bump score.
    if is_prompt_injection(content):
        abuse = AbuseDetectionService(db)
        await abuse.record_inline_flag(
            user_id=user.id,
            ip=remote_ip,
            pattern="prompt_injection",
            score=SCORE_PROMPT_INJECTION,
            details={"sample": content[:120]},
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "prompt_injection_blocked",
                "message": "Nội dung không hợp lệ.",
            },
        )

    # 4. CAPTCHA when required.
    if user.chat_captcha_required:
        ok = await verify_chat_captcha(db, user.id, captcha_token, remote_ip)
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "captcha_required",
                    "message": "Vui lòng xác nhận bạn không phải robot.",
                },
            )
        await db.commit()


__all__ = ["run_hardening_gates"]
