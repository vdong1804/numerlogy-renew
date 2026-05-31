"""User domain service: lookup, creation, password updates."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.models.user import User, UserProfile


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Return User matching email, or None."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Return User matching id, or None."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    email: str,
    password: str,
    first_name: str = "",
    last_name: str = "",
) -> User:
    """Create User + UserProfile in a single transaction.

    Args:
        db: Async DB session (caller commits).
        email: Unique email address.
        password: Plain-text password (hashed before persist).
        first_name: Optional first name.
        last_name: Optional last name.

    Returns:
        Newly created and flushed User (id populated).
    """
    user = User(
        email=email,
        hashed_password=hash_password(password),
        first_name=first_name,
        last_name=last_name,
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    await db.flush()  # populate user.id before creating profile

    profile = UserProfile(
        user_id=user.id,
        name=f"{first_name} {last_name}".strip() or email,
    )
    db.add(profile)
    await db.flush()
    return user


async def update_user_password(db: AsyncSession, user: User, new_password: str) -> None:
    """Hash and persist a new password on the given user row."""
    user.hashed_password = hash_password(new_password)
    db.add(user)
    await db.flush()
