"""slowapi rate limiter setup.

Key function behaviour depends on TRUSTED_PROXY_MODE:
- "cloudflare" (default): only trust CF-Connecting-IP; ignore X-Forwarded-For to prevent
  IP spoofing when Cloudflare is in proxy mode. Falls back to request.client.host if the
  header is absent (e.g. health-check from localhost).
- "direct": use request.client.host directly (nginx terminates TLS, no Cloudflare proxy).

When RATE_LIMIT_ENABLED=false (test env), Limiter.enabled=False makes all
@limiter.limit decorators no-ops — prevents flaky tests from shared counters.
"""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings


def _cf_ip_key(request: Request) -> str:
    """Return rate-limit key IP based on TRUSTED_PROXY_MODE setting."""
    if settings.trusted_proxy_mode == "cloudflare":
        # Only trust the header Cloudflare injects; never fall back to XFF
        # (XFF is attacker-controlled when Cloudflare is in DNS-only mode).
        return (
            request.headers.get("CF-Connecting-IP")
            or get_remote_address(request)
        )
    # "direct" mode: nginx → uvicorn, no Cloudflare proxy layer
    return get_remote_address(request)


# enabled=False turns all @limiter.limit() decorators into no-ops (test env safe)
limiter = Limiter(
    key_func=_cf_ip_key,
    default_limits=[],
    enabled=settings.rate_limit_enabled,
)
