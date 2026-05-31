"""HMAC-SHA256 signed tokens for unauthenticated PDF download links.

Token format (URL-safe base64): <base64(json_payload)>.<base64(signature)>
Payload: {"typ": "report_download", "user_report_id": int, "exp": unix_timestamp}
Secret: settings.jwt_secret (reuse — no extra env var needed per locked decisions)
Expiry: 7 days default
"""

import base64
import hashlib
import hmac
import json
import time
from typing import Optional

from app.config import settings

_TOKEN_TYPE = "report_download"


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64_decode(s: str) -> bytes:
    # Re-pad
    pad = 4 - len(s) % 4
    if pad != 4:
        s += "=" * pad
    return base64.urlsafe_b64decode(s)


def _sign(payload_b64: str, secret: str) -> str:
    sig = hmac.new(secret.encode(), payload_b64.encode(), hashlib.sha256).digest()
    return _b64_encode(sig)


def make_signed_token(user_report_id: int, expires_in_seconds: int = 7 * 24 * 3600) -> str:
    """Return a signed token for a user_report download link."""
    payload = {
        "typ": _TOKEN_TYPE,
        "user_report_id": user_report_id,
        "exp": int(time.time()) + expires_in_seconds,
    }
    payload_b64 = _b64_encode(json.dumps(payload, separators=(",", ":")).encode())
    sig = _sign(payload_b64, settings.jwt_secret)
    return f"{payload_b64}.{sig}"


def verify_signed_token(token: str) -> Optional[int]:
    """Verify token and return user_report_id, or None if invalid/expired."""
    try:
        payload_b64, sig = token.rsplit(".", 1)
    except ValueError:
        return None

    expected_sig = _sign(payload_b64, settings.jwt_secret)
    if not hmac.compare_digest(expected_sig, sig):
        return None

    try:
        payload = json.loads(_b64_decode(payload_b64))
    except Exception:  # noqa: BLE001
        return None

    # Reject tokens not issued for report downloads (typ discriminator)
    if payload.get("typ") != _TOKEN_TYPE:
        return None

    if payload.get("exp", 0) < time.time():
        return None

    user_report_id = payload.get("user_report_id")
    if not isinstance(user_report_id, int):
        return None

    return user_report_id
