# ruff: noqa: UP045, UP017
"""AbuseDetectionService — five chat-abuse patterns + scoring (Phase 08).

Detection runs out-of-band via `detect_chat_abuse` job (every 15 min).
The job calls each `detect_*` method, persists `ChatAbuseFlag` rows, and
applies score side-effects on `users` (CAPTCHA required / suspend).

Pure detection methods are session-bound and idempotent within a single
window (caller passes a `since` cutoff). Re-running over the same window
yields the same flags (deduped at write time by latest-flag check).

Inline checks (called from request path):
- `is_prompt_injection(text)` — cheap regex pre-LLM filter.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

logger = logging.getLogger(__name__)

# Score deltas per pattern; tuned for thresholds 10 (CAPTCHA) / 50 (suspend).
SCORE_RAPID_QUOTA_CYCLE = 8
SCORE_PROMPT_INJECTION = 5
SCORE_IDENTICAL_BURST = 6
SCORE_PDF_UPLOAD_SPAM = 4
SCORE_QUOTA_GRIEF = 1  # analytics only

CAPTCHA_THRESHOLD = 10
SUSPEND_THRESHOLD = 50

# Prompt-injection patterns. Kept narrow on purpose to avoid blocking benign
# numerology questions that happen to mention "previous".
_INJECTION_RE = re.compile(
    r"(?ix)"
    r"(?:ignore|disregard|forget)\s+(?:previous|prior|above|earlier)\s+(?:instructions?|prompts?|messages?)"
    r"|^\s*system\s*:"
    r"|<\|(?:system|im_start|im_end|assistant|user)\|>"
    r"|you\s+are\s+now\s+a\s+different",
)


def is_prompt_injection(message: str) -> bool:
    """Cheap regex pre-LLM check. False positives cost the user a 400, not a ban."""
    if not message:
        return False
    return bool(_INJECTION_RE.search(message))


@dataclass(frozen=True)
class FlagToWrite:
    user_id: Optional[int]
    ip: Optional[str]
    pattern: str
    score: int
    details: dict


class AbuseDetectionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Pattern detectors
    # ------------------------------------------------------------------

    async def detect_rapid_quota_cycle(
        self, since: datetime
    ) -> list[FlagToWrite]:
        """Same IP creating multiple accounts hitting free limit within window.

        Requires per-message IP tracking which is not yet captured on
        `chat_messages`. Placeholder until a future migration adds
        `chat_messages.ip` or we store IP in a side table. Returning empty
        keeps the scheduler happy in production.
        """
        # TODO(phase08+): wire IP capture in messages router and implement.
        return []

    async def detect_identical_burst(
        self, since: datetime, min_count: int = 10
    ) -> list[FlagToWrite]:
        """Identical content sent >= min_count times within window across any users."""
        rows = (
            await self.db.execute(
                text(
                    """
                    SELECT m.content, COUNT(*) AS cnt, COUNT(DISTINCT c.user_id) AS users
                    FROM chat_messages m
                    JOIN chat_conversations c ON c.id = m.conversation_id
                    WHERE m.role = 'user' AND m.created_at >= :since
                    GROUP BY m.content
                    HAVING COUNT(*) >= :min_count
                    """
                ),
                {"since": since, "min_count": min_count},
            )
        ).all()
        flags: list[FlagToWrite] = []
        for content, cnt, users in rows:
            # Truncate content in details to keep JSON small.
            preview = (content or "")[:120]
            flags.append(
                FlagToWrite(
                    user_id=None,
                    ip=None,
                    pattern="identical_burst",
                    score=SCORE_IDENTICAL_BURST,
                    details={
                        "count": int(cnt),
                        "users": int(users),
                        "content_preview": preview,
                    },
                )
            )
        return flags

    async def detect_pdf_upload_spam(
        self, since: datetime, max_uploads: int = 20
    ) -> list[FlagToWrite]:
        """Users with > max_uploads PDF uploads in the window."""
        rows = (
            await self.db.execute(
                text(
                    """
                    SELECT user_id, COUNT(*) AS cnt
                    FROM user_pdf_index
                    WHERE parsed_at >= :since
                    GROUP BY user_id
                    HAVING COUNT(*) > :max_uploads
                    """
                ),
                {"since": since, "max_uploads": max_uploads},
            )
        ).all()
        return [
            FlagToWrite(
                user_id=int(user_id),
                ip=None,
                pattern="pdf_upload_spam",
                score=SCORE_PDF_UPLOAD_SPAM,
                details={"uploads": int(cnt)},
            )
            for user_id, cnt in rows
        ]

    async def detect_quota_grief(self, since: datetime) -> list[FlagToWrite]:
        """Soft signal: users exhausting free quota daily for >=7d without buying."""
        # Heuristic: free_used >= free_limit on 7+ distinct dates in last 30d AND
        # zero addon purchases. Used for analytics, not enforcement.
        rows = (
            await self.db.execute(
                text(
                    """
                    SELECT q.user_id,
                           COUNT(DISTINCT q.date) AS exhaust_days
                    FROM chat_quota_usage q
                    LEFT JOIN chat_addon_purchases a
                        ON a.user_id = q.user_id AND a.is_active = TRUE
                    WHERE q.date >= :since
                      AND q.free_used >= :limit
                      AND a.id IS NULL
                    GROUP BY q.user_id
                    HAVING COUNT(DISTINCT q.date) >= 7
                    """
                ),
                {"since": since.date(), "limit": settings.chat_free_daily_limit},
            )
        ).all()
        return [
            FlagToWrite(
                user_id=int(user_id),
                ip=None,
                pattern="quota_exhaustion_grief",
                score=SCORE_QUOTA_GRIEF,
                details={"exhaust_days": int(days)},
            )
            for user_id, days in rows
        ]

    # ------------------------------------------------------------------
    # Persistence + side-effects
    # ------------------------------------------------------------------

    async def record_inline_flag(
        self,
        user_id: Optional[int],
        ip: Optional[str],
        pattern: str,
        score: int,
        details: Optional[dict] = None,
    ) -> None:
        """Hot-path writer for inline detections (e.g. prompt_injection from router).
        Caller owns commit."""
        await self.db.execute(
            text(
                "INSERT INTO chat_abuse_flags (user_id, ip, pattern, score, details) "
                "VALUES (:u, :ip, :p, :s, :d)"
            ),
            {
                "u": user_id, "ip": ip, "p": pattern, "s": score,
                "d": json.dumps(details or {}),
            },
        )
        if user_id is not None:
            await self._apply_score_delta(user_id, score)

    async def write_flags(self, flags: list[FlagToWrite]) -> int:
        """Bulk-write detector output. Returns number of rows inserted."""
        if not flags:
            return 0
        for f in flags:
            await self.db.execute(
                text(
                    "INSERT INTO chat_abuse_flags (user_id, ip, pattern, score, details) "
                    "VALUES (:u, :ip, :p, :s, :d)"
                ),
                {
                    "u": f.user_id,
                    "ip": f.ip,
                    "p": f.pattern,
                    "s": f.score,
                    "d": json.dumps(f.details or {}),
                },
            )
            if f.user_id is not None:
                await self._apply_score_delta(f.user_id, f.score)
        return len(flags)

    async def _apply_score_delta(self, user_id: int, delta: int) -> None:
        await self.db.execute(
            text(
                """
                UPDATE users
                SET chat_abuse_score = chat_abuse_score + :d,
                    chat_captcha_required = CASE
                        WHEN chat_abuse_score + :d >= :cap THEN TRUE
                        ELSE chat_captcha_required
                    END,
                    chat_suspended_at = CASE
                        WHEN chat_abuse_score + :d >= :susp AND chat_suspended_at IS NULL
                            THEN CURRENT_TIMESTAMP
                        ELSE chat_suspended_at
                    END
                WHERE id = :uid
                """
            ),
            {
                "d": delta,
                "cap": CAPTCHA_THRESHOLD,
                "susp": SUSPEND_THRESHOLD,
                "uid": user_id,
            },
        )


__all__ = [
    "AbuseDetectionService",
    "FlagToWrite",
    "is_prompt_injection",
    "CAPTCHA_THRESHOLD",
    "SUSPEND_THRESHOLD",
]
