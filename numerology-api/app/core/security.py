"""Security helpers: password hashing, JWT encode/decode, refresh token hashing."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# bcrypt with 12 rounds (default for passlib bcrypt)
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# Password utilities
# ---------------------------------------------------------------------------


def hash_password(plain: str) -> str:
    """Return bcrypt hash of plain-text password."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches stored bcrypt hash."""
    return _pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT utilities
# ---------------------------------------------------------------------------


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def create_access_token(sub: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a short-lived JWT access token.

    Args:
        sub: Subject claim — must be str(user.id).
        expires_delta: Override default expiry (default: ACCESS_TOKEN_EXPIRE_MINUTES).
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    expire = _utc_now() + expires_delta
    payload = {"sub": sub, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(sub: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a long-lived JWT refresh token (raw value — hash before storing).

    The `jti` claim guarantees uniqueness so rapid rotations within the same
    second produce distinct tokens (and distinct stored hashes).

    Args:
        sub: Subject claim — str(user.id).
        expires_delta: Override default expiry (default: REFRESH_TOKEN_EXPIRE_DAYS).
    """
    if expires_delta is None:
        expires_delta = timedelta(days=settings.refresh_token_expire_days)
    expire = _utc_now() + expires_delta
    payload = {
        "sub": sub,
        "exp": expire,
        "type": "refresh",
        "jti": secrets.token_hex(8),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT. Raises JWTError on failure.

    Returns:
        Decoded payload dict (contains 'sub', 'exp', 'type').
    """
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise


# ---------------------------------------------------------------------------
# Refresh token storage helpers
# ---------------------------------------------------------------------------


def hash_refresh_token(raw_token: str) -> str:
    """Return SHA-256 hex digest of raw refresh token (stored in DB, not raw)."""
    return hashlib.sha256(raw_token.encode()).hexdigest()
