# ruff: noqa: UP045
"""Network utilities — client IP extraction for rate limiting."""

from __future__ import annotations

from fastapi import Request


def get_client_ip(request: Request) -> str:
    """Extract real client IP from request headers.

    Priority:
    1. X-Real-IP (set by Nginx proxy_pass)
    2. X-Forwarded-For first entry (load-balancer chain)
    3. request.client.host (direct connection)
    """
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client:
        return request.client.host

    return "unknown"
