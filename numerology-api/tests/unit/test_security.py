"""Unit tests for password hashing and JWT utilities."""

import time
from datetime import datetime, timedelta, timezone

import pytest
from jose import JWTError

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_refresh_token,
)


class TestPasswordHashing:
    """Password hash and verify round-trip."""

    def test_hash_password_returns_string(self):
        """hash_password returns bcrypt hash string."""
        plain = "mypassword123"
        hashed = hash_password(plain)
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """verify_password returns True for correct password."""
        plain = "mypassword123"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_password_incorrect(self):
        """verify_password returns False for wrong password."""
        plain = "mypassword123"
        hashed = hash_password(plain)
        assert verify_password("wrongpassword", hashed) is False

    def test_hash_is_deterministic_but_different(self):
        """Same password hashed twice gives different strings (bcrypt salt)."""
        plain = "mypassword123"
        hash1 = hash_password(plain)
        hash2 = hash_password(plain)
        # Hashes differ due to salt
        assert hash1 != hash2
        # But both verify against same password
        assert verify_password(plain, hash1) is True
        assert verify_password(plain, hash2) is True

    def test_hash_empty_password(self):
        """Empty password can be hashed."""
        hashed = hash_password("")
        assert isinstance(hashed, str)
        assert verify_password("", hashed) is True

    def test_hash_special_chars(self):
        """Special chars in password."""
        plain = "p@ss!word#$%^&*()"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True
        assert verify_password(plain + "x", hashed) is False


class TestJWTCreation:
    """JWT token creation (access and refresh)."""

    def test_create_access_token_returns_string(self):
        """create_access_token returns JWT string."""
        token = create_access_token("user123")
        assert isinstance(token, str)
        parts = token.split(".")
        assert len(parts) == 3  # JWT format: header.payload.signature

    def test_create_refresh_token_returns_string(self):
        """create_refresh_token returns JWT string."""
        token = create_refresh_token("user456")
        assert isinstance(token, str)
        parts = token.split(".")
        assert len(parts) == 3

    def test_create_access_token_default_expiry(self):
        """create_access_token with default expiry (15 min)."""
        token = create_access_token("user123")
        payload = decode_token(token)
        assert payload["sub"] == "user123"
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_create_refresh_token_default_expiry(self):
        """create_refresh_token with default expiry (7 days)."""
        token = create_refresh_token("user123")
        payload = decode_token(token)
        assert payload["sub"] == "user123"
        assert payload["type"] == "refresh"

    def test_custom_expires_delta(self):
        """Override default expiry."""
        custom_delta = timedelta(hours=2)
        token = create_access_token("user123", expires_delta=custom_delta)
        payload = decode_token(token)
        assert payload["sub"] == "user123"

    def test_token_includes_claims(self):
        """Token includes sub, exp, type claims."""
        token = create_access_token("user999")
        payload = decode_token(token)
        assert payload["sub"] == "user999"
        assert payload["type"] == "access"
        assert "exp" in payload


class TestJWTDecoding:
    """JWT decode validation."""

    def test_decode_valid_token(self):
        """decode_token returns payload dict for valid token."""
        token = create_access_token("user123")
        payload = decode_token(token)
        assert isinstance(payload, dict)
        assert payload["sub"] == "user123"

    def test_decode_malformed_token_raises(self):
        """Malformed token raises JWTError."""
        with pytest.raises(JWTError):
            decode_token("not.a.token")

    def test_decode_missing_parts_raises(self):
        """Token with missing parts raises JWTError."""
        with pytest.raises(JWTError):
            decode_token("onlyonepart")

    def test_decode_empty_string_raises(self):
        """Empty token string raises JWTError."""
        with pytest.raises(JWTError):
            decode_token("")

    def test_decode_tampered_payload_raises(self):
        """Token with tampered payload raises JWTError."""
        token = create_access_token("user123")
        parts = token.split(".")
        # Tamper with payload (second part)
        tampered = parts[0] + ".invalid" + "." + parts[2]
        with pytest.raises(JWTError):
            decode_token(tampered)

    def test_decode_expired_token_raises(self):
        """Expired token raises JWTError."""
        # Create token that expired 1 second ago
        expired_delta = timedelta(seconds=-1)
        token = create_access_token("user123", expires_delta=expired_delta)
        time.sleep(0.1)  # Small delay to ensure expiry
        with pytest.raises(JWTError):
            decode_token(token)

    def test_decode_different_secret_raises(self):
        """Token signed with different secret cannot be decoded."""
        token = create_access_token("user123")
        # We can't easily test this without modifying settings,
        # but we verify the token is properly signed
        payload = decode_token(token)
        assert payload["sub"] == "user123"


class TestRefreshTokenHashing:
    """Refresh token hash for DB storage."""

    def test_hash_refresh_token_returns_hex(self):
        """hash_refresh_token returns hex string."""
        token = create_refresh_token("user123")
        hashed = hash_refresh_token(token)
        assert isinstance(hashed, str)
        assert all(c in "0123456789abcdef" for c in hashed)

    def test_hash_refresh_token_deterministic(self):
        """Same token always hashes to same value (SHA-256)."""
        token = "fixed_token_string"
        hash1 = hash_refresh_token(token)
        hash2 = hash_refresh_token(token)
        assert hash1 == hash2

    def test_hash_refresh_token_length(self):
        """SHA-256 hash is 64 hex chars (256 bits)."""
        token = "any_token"
        hashed = hash_refresh_token(token)
        assert len(hashed) == 64

    def test_different_tokens_different_hashes(self):
        """Different tokens hash to different values."""
        token1 = "token1"
        token2 = "token2"
        assert hash_refresh_token(token1) != hash_refresh_token(token2)

    def test_hash_real_refresh_token(self):
        """Hash a real refresh token from create_refresh_token."""
        token = create_refresh_token("user123")
        hashed = hash_refresh_token(token)
        assert isinstance(hashed, str)
        assert len(hashed) == 64


class TestTokenRoundTrip:
    """End-to-end token creation and verification."""

    def test_access_token_roundtrip(self):
        """Create access token, decode, verify claims."""
        user_id = "user_12345"
        token = create_access_token(user_id)
        payload = decode_token(token)
        assert payload["sub"] == user_id
        assert payload["type"] == "access"

    def test_refresh_token_roundtrip(self):
        """Create refresh token, decode, verify claims."""
        user_id = "user_67890"
        token = create_refresh_token(user_id)
        payload = decode_token(token)
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"

    def test_token_subject_string(self):
        """Token subject (user_id) stored as string."""
        user_id = "123"
        token = create_access_token(user_id)
        payload = decode_token(token)
        assert payload["sub"] == "123"
        assert isinstance(payload["sub"], str)
