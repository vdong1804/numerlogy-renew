"""Pytest fixtures for async tests: DB, client, auth users, mocks."""

import asyncio
from typing import AsyncGenerator

import httpx
import pytest
import respx
from sqlalchemy import BigInteger
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.models.auth import RefreshToken
from app.db.models.user import User, UserProfile
from app.main import create_app
from app.deps import get_db


# SQLite only autoincrements on INTEGER PRIMARY KEY (not BIGINT).
# Render BigInteger as INTEGER on SQLite so id columns autoincrement in tests.
@compiles(BigInteger, "sqlite")
def _sqlite_bigint_as_integer(element, compiler, **kw):  # noqa: D401
    return "INTEGER"


# ---------------------------------------------------------------------------
# Event loop (session-scope)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def event_loop():
    """Provide event loop for entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# Test DB engine & session factory (with in-memory SQLite)
# ---------------------------------------------------------------------------


@pytest.fixture
async def engine():
    """In-memory async SQLite engine for tests."""
    # aiosqlite:///:memory: is an in-memory DB, StaticPool prevents GC
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"timeout": 15},
        poolclass=StaticPool,
        echo=False,
    )
    # Create tables (no Alembic in tests)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    await test_engine.dispose()


@pytest.fixture
async def db_session_factory(engine):
    """Async sessionmaker factory."""
    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return async_session


@pytest.fixture
async def db_session(db_session_factory) -> AsyncGenerator[AsyncSession, None]:
    """Fresh async session for each test with rollback on teardown."""
    session = db_session_factory()
    try:
        yield session
    finally:
        await session.rollback()
        await session.close()


# ---------------------------------------------------------------------------
# FastAPI app with overridden DB dependency
# ---------------------------------------------------------------------------


@pytest.fixture
def app(db_session_factory):
    """FastAPI app with test DB session override."""
    test_app = create_app()

    async def override_get_db():
        session = db_session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    test_app.dependency_overrides[get_db] = override_get_db
    return test_app


@pytest.fixture
async def client(app):
    """Async HTTP client for testing endpoints."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# Test users & auth fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def superuser(db_session: AsyncSession) -> User:
    """Create a superuser for admin tests."""
    user = User(
        email="admin@test.com",
        hashed_password=hash_password("admin123"),
        first_name="Admin",
        last_name="User",
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def user(db_session: AsyncSession) -> User:
    """Create a regular user."""
    user_obj = User(
        email="user@test.com",
        hashed_password=hash_password("password123"),
        first_name="Test",
        last_name="User",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user_obj)
    await db_session.flush()
    await db_session.refresh(user_obj)
    return user_obj


@pytest.fixture
async def user_with_profile(db_session: AsyncSession, user: User) -> User:
    """User with profile and quota."""
    profile = UserProfile(
        user_id=user.id,
        name="Nguyen Van A",
        birth_day="15101990",
        phone="0901234567",
        number_download=5,
    )
    db_session.add(profile)
    await db_session.commit()
    user.profile = profile
    return user


@pytest.fixture
async def user_no_quota(db_session: AsyncSession) -> User:
    """User with 0 downloads remaining."""
    u = User(
        email="noquota@test.com",
        hashed_password=hash_password("pass"),
        first_name="No",
        last_name="Quota",
        is_active=True,
    )
    db_session.add(u)
    await db_session.flush()
    await db_session.refresh(u)

    profile = UserProfile(
        user_id=u.id,
        name="No Quota User",
        birth_day="01011990",
        number_download=0,
    )
    db_session.add(profile)
    await db_session.flush()
    return u


@pytest.fixture
async def auth_headers(user: User) -> dict[str, str]:
    """Bearer token for regular user."""
    token = create_access_token(str(user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def superuser_headers(superuser: User) -> dict[str, str]:
    """Bearer token for superuser."""
    token = create_access_token(str(superuser.id))
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Mock external services (respx)
# ---------------------------------------------------------------------------


@pytest.fixture
async def mock_horoscope(respx_mock):
    """Mock vietheart.net horoscope endpoint."""
    respx_mock.post("https://www.vietheart.net/api/horoscope/get_detail").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": "<svg xmlns='http://www.w3.org/2000/svg'></svg>",
                "status": 1,
            },
        )
    )
    return respx_mock


@pytest.fixture
async def mock_pdf(monkeypatch):
    """Mock PDF rendering (wkhtmltopdf may not be available in tests)."""
    def mock_render(html: str, **kwargs) -> bytes:
        return b"%PDF-1.4 mock\n%Mock PDF stub for testing\n" + html.encode()[:100]

    monkeypatch.setattr("app.utils.pdf.render_pdf", mock_render)
