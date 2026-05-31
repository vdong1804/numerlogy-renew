"""Password reset token domain service: issue, validate, consume."""

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import hash_refresh_token  # SHA-256 hex helper (reused)
from app.db.models.auth import PasswordResetToken, RefreshToken


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _hash(raw: str) -> str:
    # Reuse SHA-256 helper from core.security
    return hash_refresh_token(raw)


async def create_reset_token(db: AsyncSession, user_id: int) -> str:
    """Issue a new password reset token (raw returned, hash stored).

    Marks any previously unused tokens for this user as consumed so a single
    user can only ever hold one outstanding reset link.

    Args:
        db: Async DB session (caller commits).
        user_id: Target user.

    Returns:
        Raw token string to embed in the email reset link.
    """
    now = _utc_now()
    # Invalidate any prior outstanding reset tokens for this user
    await db.execute(
        update(PasswordResetToken)
        .where(
            and_(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.used_at.is_(None),
            )
        )
        .values(used_at=now)
    )

    raw = secrets.token_urlsafe(32)
    expires_at = now + timedelta(
        minutes=settings.password_reset_token_expire_minutes
    )
    row = PasswordResetToken(
        user_id=user_id,
        token_hash=_hash(raw),
        expires_at=expires_at,
    )
    db.add(row)
    await db.flush()
    return raw


async def consume_reset_token(db: AsyncSession, raw_token: str) -> int:
    """Validate a reset token, mark as used, and return owning user_id.

    Raises ValueError on invalid / expired / already-used tokens.
    """
    token_hash = _hash(raw_token)
    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )
    row = result.scalar_one_or_none()

    if row is None:
        raise ValueError("Invalid reset token")
    if row.used_at is not None:
        raise ValueError("Reset token already used")
    # SQLite returns naive datetimes; assume stored values are UTC
    expires_at = row.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < _utc_now():
        raise ValueError("Reset token expired")

    row.used_at = _utc_now()
    db.add(row)
    await db.flush()
    return row.user_id


async def revoke_all_user_refresh_tokens(db: AsyncSession, user_id: int) -> None:
    """Revoke every active refresh token for a user (force re-login)."""
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=_utc_now())
    )
    await db.flush()
