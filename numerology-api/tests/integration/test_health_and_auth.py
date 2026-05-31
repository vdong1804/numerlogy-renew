"""Integration tests for health endpoint and auth flow."""

import pytest


class TestHealth:
    """Health check endpoint."""

    async def test_health_endpoint(self, client):
        """GET /health returns 200 with status ok."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data == {"status": "ok"}


class TestAuthRegister:
    """POST /auth/register endpoint."""

    async def test_register_happy_path(self, client, db_session):
        """Register new user returns 201 with tokens."""
        response = await client.post(
            "/auth/register",
            json={
                "email": "newuser@test.com",
                "password": "password123",
                "first_name": "New",
                "last_name": "User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_duplicate_email_conflict(self, client, user):
        """Register with existing email returns 409."""
        response = await client.post(
            "/auth/register",
            json={
                "email": user.email,
                "password": "newpassword",
                "first_name": "Duplicate",
                "last_name": "User",
            },
        )
        assert response.status_code == 409
        assert "already registered" in response.json()["detail"].lower()

    async def test_register_missing_field(self, client):
        """Register missing required field returns 422."""
        response = await client.post(
            "/auth/register",
            json={"email": "test@test.com"},  # Missing password, names
        )
        assert response.status_code == 422


class TestAuthLogin:
    """POST /auth/login endpoint."""

    async def test_login_happy_path(self, client, user):
        """Login with correct credentials returns tokens."""
        response = await client.post(
            "/auth/login",
            json={
                "email": user.email,
                "password": "password123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_wrong_password(self, client, user):
        """Login with wrong password returns 401."""
        response = await client.post(
            "/auth/login",
            json={
                "email": user.email,
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    async def test_login_nonexistent_user(self, client):
        """Login with non-existent email returns 401."""
        response = await client.post(
            "/auth/login",
            json={
                "email": "nonexistent@test.com",
                "password": "anypassword",
            },
        )
        assert response.status_code == 401

    async def test_login_disabled_user(self, client, db_session, user):
        """Login disabled user returns 403."""
        user.is_active = False
        db_session.add(user)
        await db_session.commit()

        response = await client.post(
            "/auth/login",
            json={
                "email": user.email,
                "password": "password123",
            },
        )
        assert response.status_code == 403
        assert "disabled" in response.json()["detail"].lower()


class TestAuthMe:
    """GET /auth/me endpoint."""

    async def test_me_without_bearer_unauthorized(self, client):
        """GET /auth/me without token returns 401."""
        response = await client.get("/auth/me")
        assert response.status_code == 401

    async def test_me_with_invalid_token(self, client):
        """GET /auth/me with invalid token returns 401."""
        response = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401

    async def test_me_with_valid_token(self, client, user, auth_headers):
        """GET /auth/me with valid token returns user data."""
        response = await client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user.id
        assert data["email"] == user.email


class TestAuthRefresh:
    """POST /auth/refresh endpoint."""

    async def test_refresh_with_valid_token(self, client, user, db_session):
        """Refresh with valid refresh token returns new pair."""
        # First login to get tokens
        login_resp = await client.post(
            "/auth/login",
            json={"email": user.email, "password": "password123"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        # Now refresh
        response = await client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # New refresh token should differ from old
        assert data["refresh_token"] != refresh_token

    async def test_refresh_with_invalid_token(self, client):
        """Refresh with invalid token returns 401."""
        response = await client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )
        assert response.status_code == 401

    async def test_refresh_with_revoked_token(self, client, user, db_session):
        """Refresh with revoked token returns 401."""
        from datetime import datetime, timedelta, timezone

        from app.core.security import create_refresh_token, hash_refresh_token
        from app.db.models.auth import RefreshToken

        refresh_token = create_refresh_token(str(user.id))
        hashed = hash_refresh_token(refresh_token)
        now = datetime.now(tz=timezone.utc)
        revoked = RefreshToken(
            user_id=user.id,
            token_hash=hashed,
            expires_at=now + timedelta(days=7),
            revoked_at=now,
        )
        db_session.add(revoked)
        await db_session.commit()

        response = await client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 401


class TestAuthLogout:
    """POST /auth/logout endpoint."""

    async def test_logout_valid_token(self, client, user):
        """Logout with valid refresh token returns 204."""
        login_resp = await client.post(
            "/auth/login",
            json={"email": user.email, "password": "password123"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        response = await client.post(
            "/auth/logout",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 204

    async def test_logout_invalid_token_idempotent(self, client):
        """Logout with invalid token (idempotent)."""
        response = await client.post(
            "/auth/logout",
            json={"refresh_token": "any.invalid.token"},
        )
        # Should be idempotent (not fail)
        assert response.status_code in [204, 401]


class TestAuthForgotPassword:
    """POST /auth/forgot-password endpoint."""

    async def test_forgot_password_unknown_email_returns_202(self, client):
        """Unknown email still returns 202 (no enumeration)."""
        response = await client.post(
            "/auth/forgot-password",
            json={"email": "nobody@test.com"},
        )
        assert response.status_code == 202

    async def test_forgot_password_known_email_creates_token(
        self, client, user, db_session
    ):
        """Known active email returns 202 and persists a reset token row."""
        response = await client.post(
            "/auth/forgot-password",
            json={"email": user.email},
        )
        assert response.status_code == 202

        from sqlalchemy import select
        from app.db.models.auth import PasswordResetToken

        result = await db_session.execute(
            select(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
        )
        rows = result.scalars().all()
        assert len(rows) >= 1

    async def test_forgot_password_invalid_email_returns_422(self, client):
        """Malformed email payload triggers validation error."""
        response = await client.post(
            "/auth/forgot-password",
            json={"email": "not-an-email"},
        )
        assert response.status_code == 422


class TestAuthResetPassword:
    """POST /auth/reset-password endpoint."""

    async def _issue_token(self, db_session, user_id: int) -> str:
        from app.services.password_reset_service import create_reset_token

        raw = await create_reset_token(db_session, user_id)
        await db_session.commit()
        return raw

    async def test_reset_password_happy_path(self, client, user, db_session):
        raw = await self._issue_token(db_session, user.id)

        response = await client.post(
            "/auth/reset-password",
            json={"token": raw, "new_password": "new-strong-pw-1"},
        )
        assert response.status_code == 204

        # Old password should no longer authenticate
        bad = await client.post(
            "/auth/login",
            json={"email": user.email, "password": "password123"},
        )
        assert bad.status_code == 401

        # New password works
        good = await client.post(
            "/auth/login",
            json={"email": user.email, "password": "new-strong-pw-1"},
        )
        assert good.status_code == 200

    async def test_reset_password_invalid_token(self, client):
        response = await client.post(
            "/auth/reset-password",
            json={"token": "does-not-exist", "new_password": "anotherpw1"},
        )
        assert response.status_code == 400

    async def test_reset_password_reused_token(self, client, user, db_session):
        raw = await self._issue_token(db_session, user.id)

        first = await client.post(
            "/auth/reset-password",
            json={"token": raw, "new_password": "first-new-pw-1"},
        )
        assert first.status_code == 204

        second = await client.post(
            "/auth/reset-password",
            json={"token": raw, "new_password": "second-new-pw-1"},
        )
        assert second.status_code == 400

    async def test_reset_password_short_password_returns_422(
        self, client, user, db_session
    ):
        raw = await self._issue_token(db_session, user.id)
        response = await client.post(
            "/auth/reset-password",
            json={"token": raw, "new_password": "short"},
        )
        assert response.status_code == 422
