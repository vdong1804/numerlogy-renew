"""Token domain service: issue, rotate, and revoke refresh tokens."""

from datetime import datetime, timedelta, timezone

from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
)
from app.db.models.auth import RefreshToken
from app.schemas.auth import TokenOut


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


async def issue_token_pair(db: AsyncSession, user_id: int) -> TokenOut:
    """Create access + refresh tokens, persist hashed refresh token in DB.

    Args:
        db: Async DB session (caller commits).
        user_id: ID of the authenticated user.

    Returns:
        TokenOut with raw access_token and refresh_token strings.
    """
    sub = str(user_id)
    access_token = create_access_token(sub)
    raw_refresh = create_refresh_token(sub)
    token_hash = hash_refresh_token(raw_refresh)
    expires_at = _utc_now() + timedelta(days=settings.refresh_token_expire_days)

    row = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(row)
    await db.flush()

    return TokenOut(access_token=access_token, refresh_token=raw_refresh)


async def rotate_refresh(db: AsyncSession, raw_refresh: str) -> TokenOut:
    """Validate refresh token, revoke it, and issue a new token pair.

    Args:
        db: Async DB session (caller commits).
        raw_refresh: Raw refresh JWT string from client.

    Returns:
        New TokenOut.

    Raises:
        ValueError: Token invalid, expired, revoked, or not found in DB.
    """
    try:
        from app.core.security import decode_token
        payload = decode_token(raw_refresh)
    except JWTError as exc:
        raise ValueError("Invalid refresh token") from exc

    if payload.get("type") != "refresh":
        raise ValueError("Token is not a refresh token")

    token_hash = hash_refresh_token(raw_refresh)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    row = result.scalar_one_or_none()

    if row is None:
        raise ValueError("Refresh token not found")
    if row.revoked_at is not None:
        raise ValueError("Refresh token already revoked")
    # SQLite returns naive datetimes; assume stored values are UTC
    expires_at = row.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < _utc_now():
        raise ValueError("Refresh token expired")

    # Revoke old token
    row.revoked_at = _utc_now()
    db.add(row)
    await db.flush()

    # Issue new pair for same user
    return await issue_token_pair(db, row.user_id)


async def revoke_refresh(db: AsyncSession, raw_refresh: str) -> None:
    """Mark refresh token as revoked (logout).

    Silently ignores tokens not found in DB (idempotent).

    Args:
        db: Async DB session (caller commits).
        raw_refresh: Raw refresh JWT string from client.
    """
    token_hash = hash_refresh_token(raw_refresh)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    row = result.scalar_one_or_none()
    if row and row.revoked_at is None:
        row.revoked_at = _utc_now()
        db.add(row)
        await db.flush()
