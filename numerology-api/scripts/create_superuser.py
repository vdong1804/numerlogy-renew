"""CLI script to create a superuser account.

Usage:
    python -m scripts.create_superuser --email admin@example.com --password Admin123!
    python -m scripts.create_superuser --email admin@example.com --password Admin123! \\
        --first-name Admin --last-name User --force
"""

import argparse
import asyncio
import re
import sys

from passlib.context import CryptContext
from sqlalchemy import select

from app.db.models.user import User, UserProfile
from scripts._db import get_session

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def _validate_args(email: str, password: str) -> None:
    if not _EMAIL_RE.match(email):
        print(f"ERROR: Invalid email format: {email}", file=sys.stderr)
        sys.exit(1)
    if len(password) < 8:
        print("ERROR: Password must be at least 8 characters", file=sys.stderr)
        sys.exit(1)


async def create_superuser(
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    force: bool = False,
) -> None:
    _validate_args(email, password)
    hashed = _hash_password(password)

    async with get_session() as db:
        result = await db.execute(select(User).where(User.email == email))
        existing: User | None = result.scalar_one_or_none()

        if existing is not None and not force:
            print(f"ERROR: User '{email}' already exists (id={existing.id}). Use --force to update.", file=sys.stderr)
            sys.exit(1)

        if existing is not None and force:
            existing.hashed_password = hashed
            existing.first_name = first_name
            existing.last_name = last_name
            existing.is_superuser = True
            existing.is_active = True
            await db.commit()
            await db.refresh(existing)
            print(f"[UPDATED] Superuser '{email}' updated (id={existing.id})")
            return

        # Create new user
        user = User(
            email=email,
            hashed_password=hashed,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            is_superuser=True,
        )
        db.add(user)
        await db.flush()  # get user.id before profile insert

        profile = UserProfile(
            user_id=user.id,
            name=f"{first_name} {last_name}".strip(),
            number_download=0,
        )
        db.add(profile)
        await db.commit()
        await db.refresh(user)
        print(f"[CREATED] Superuser '{email}' created (id={user.id})")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a superuser account")
    parser.add_argument("--email", required=True, help="Email address")
    parser.add_argument("--password", required=True, help="Password (min 8 chars)")
    parser.add_argument("--first-name", default="Admin", dest="first_name", help="First name")
    parser.add_argument("--last-name", default="", dest="last_name", help="Last name")
    parser.add_argument("--force", action="store_true", help="Update existing user instead of failing")
    return parser.parse_args()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    args = _parse_args()
    asyncio.run(create_superuser(args.email, args.password, args.first_name, args.last_name, args.force))
