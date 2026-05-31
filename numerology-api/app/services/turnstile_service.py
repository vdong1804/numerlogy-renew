# ruff: noqa: UP045, UP017
"""Cloudflare Turnstile CAPTCHA verification.

Skips verification when TURNSTILE_SECRET_KEY is empty (local dev / CI).

Phase 08: `verify_chat_captcha` extends the base verify with a chat-specific
side effect: on success, increment `users.chat_captcha_solve_count` and clear
`chat_captcha_required` once the user has solved CAPTCHA 5 times in a row.
"""

import logging
from typing import Optional

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

logger = logging.getLogger(__name__)

_TURNSTILE_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

# Phase 08: clear chat_captcha_required after N successful solves.
CHAT_CAPTCHA_CLEAR_THRESHOLD = 5


async def verify(token: Optional[str], remote_ip: Optional[str] = None) -> bool:
    """Return True if token is valid or secret key not configured (dev mode)."""
    if not settings.turnstile_secret_key:
        # Dev/CI: skip verification
        logger.debug("Turnstile verify skipped (no secret key configured)")
        return True

    if not token:
        return False

    body: dict = {"secret": settings.turnstile_secret_key, "response": token}
    if remote_ip:
        body["remoteip"] = remote_ip

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(_TURNSTILE_URL, data=body)
            resp.raise_for_status()
            data = resp.json()
            success = bool(data.get("success", False))
            if not success:
                logger.warning("Turnstile rejected token: %s", data.get("error-codes"))
            return success
    except Exception as exc:  # noqa: BLE001
        # Network failure → fail-closed (reject)
        logger.error("Turnstile verify error: %s", exc)
        return False


async def verify_chat_captcha(
    db: AsyncSession,
    user_id: int,
    token: Optional[str],
    remote_ip: Optional[str] = None,
) -> bool:
    """Verify Turnstile + bump per-user solve counter.

    On `CHAT_CAPTCHA_CLEAR_THRESHOLD` consecutive solves, clear the
    `chat_captcha_required` flag so the user no longer sees CAPTCHA. Caller
    owns commit.
    """
    ok = await verify(token, remote_ip)
    if not ok:
        return False
    # Row-level lock to serialise concurrent CAPTCHA solves — without this,
    # two parallel requests reading solve_count=4 would both INSERT 5+1 and
    # clear the flag at 2 solves instead of 5. SQLite ignores FOR UPDATE
    # (no-op in tests); PG enforces it.
    await db.execute(
        text("SELECT id FROM users WHERE id = :u FOR UPDATE"),
        {"u": user_id},
    )
    await db.execute(
        text(
            """
            UPDATE users
            SET chat_captcha_required = CASE
                    WHEN chat_captcha_solve_count + 1 >= :n THEN FALSE
                    ELSE chat_captcha_required
                END,
                chat_captcha_solve_count = CASE
                    WHEN chat_captcha_solve_count + 1 >= :n THEN 0
                    ELSE chat_captcha_solve_count + 1
                END
            WHERE id = :u
            """
        ),
        {"u": user_id, "n": CHAT_CAPTCHA_CLEAR_THRESHOLD},
    )
    return True
