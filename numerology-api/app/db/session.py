"""Async SQLAlchemy engine and session factory."""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

# Engine — pool_pre_ping avoids stale connections after DB restart
engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=settings.debug,
)

# Session factory — expire_on_commit=False keeps attrs accessible after commit
async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
