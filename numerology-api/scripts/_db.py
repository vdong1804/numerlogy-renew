"""Shared async DB session helper for seed scripts.

Usage:
    async with get_session() as db:
        await db.execute(...)
        await db.commit()
"""

import os
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://numerology:numerology@localhost:5432/numerology",
)

_engine = create_async_engine(DATABASE_URL, echo=False)
_SessionLocal = sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def get_session():
    """Async context manager yielding an AsyncSession."""
    async with _SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
