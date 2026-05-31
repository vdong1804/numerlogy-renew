"""Inbound webhook endpoints (provider machine-to-machine).

Always returns 200 (except on auth failure) so providers do not retry on
unmatched / amount-mismatch — those are logged for ops review.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.deps import get_db
from app.middleware.rate_limit import limiter
from app.schemas.webhook import SePayWebhookPayload
from app.services import sepay_service

logger = logging.getLogger(__name__)

webhooks_router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


def _check_ip_allowlist(request: Request) -> None:
    allowlist = settings.sepay_webhook_ip_whitelist
    if not allowlist:
        return  # disabled
    client_ip = (
        request.headers.get("x-forwarded-for", request.client.host if request.client else "")
        .split(",")[0]
        .strip()
    )
    if client_ip not in allowlist:
        logger.warning("Rejecting SePay webhook from unlisted IP: %s", client_ip)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="IP not allowed"
        )


@webhooks_router.post("/sepay", status_code=status.HTTP_200_OK)
@limiter.limit("100/minute")
async def sepay_webhook(
    request: Request,
    payload: SePayWebhookPayload,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    """SePay webhook receiver — auth via Apikey header, idempotent processing.

    Rate-limited 100/minute per IP — generous for legitimate SePay IPs.
    """
    _check_ip_allowlist(request)
    if not sepay_service.verify_apikey(authorization):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )

    event = await sepay_service.process_webhook(db, payload)
    return {
        "status": event.status,
        "order_id": event.order_id,
        "ref_code": event.ref_code,
    }
