# ruff: noqa: UP045, UP017, E501
"""SePay webhook handling: auth, parsing, idempotent matching.

The public entry-point is `process_webhook(...)`. It is designed to ALWAYS
commit a row to ``webhook_events`` (matched or not) so that operations
have a complete audit trail.

`list_recent_transactions(hours)` fetches the SePay transaction list API
for the reconcile cron job (never logs full tx data — only ref_code + amount).
"""

import hmac
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models.order import Order
from app.db.models.package import UserPayment
from app.db.models.webhook_event import WebhookEvent
from app.schemas.webhook import SePayWebhookPayload

logger = logging.getLogger(__name__)

# SePay transaction list API endpoint
_SEPAY_TX_LIST_URL = "https://my.sepay.vn/userapi/transactions/list"

# Strict regex with word boundaries — see Crockford alphabet in utils/ref_code.py
REF_CODE_RE = re.compile(r"\bNSQ-[A-Z0-9]{8}\b")

# Chat-addon payment marker — user enters this as bank transfer content.
# Format: CHATADDON<payment_id>  (case-insensitive, digits only)
CHATADDON_RE = re.compile(r"CHATADDON(\d+)", re.IGNORECASE)


def parse_ref_code(text: Optional[str]) -> Optional[str]:
    """Extract NSQ-XXXXXXXX from a free-form bank transfer description."""
    if not text:
        return None
    upper = text.upper()
    m = REF_CODE_RE.search(upper)
    return m.group(0) if m else None


def parse_addon_payment_id(text: Optional[str]) -> Optional[int]:
    """Extract integer payment_id from CHATADDON<id> in transfer content."""
    if not text:
        return None
    m = CHATADDON_RE.search(text)
    return int(m.group(1)) if m else None


def verify_apikey(provided: Optional[str]) -> bool:
    """Constant-time comparison against the configured SePay API key.

    Accepts either ``Apikey <key>`` or raw ``<key>`` formats.
    Returns False if SEPAY_API_KEY is not configured (deny by default).
    """
    expected = settings.sepay_api_key
    if not expected or not provided:
        return False
    token = provided.strip()
    if token.lower().startswith("apikey "):
        token = token[7:].strip()
    return hmac.compare_digest(token, expected)


async def _create_event(
    db: AsyncSession,
    payload: SePayWebhookPayload,
    *,
    status: str,
    order_id: Optional[int] = None,
    ref_code: Optional[str] = None,
    error_message: Optional[str] = None,
) -> WebhookEvent:
    event = WebhookEvent(
        provider="sepay",
        sepay_tx_id=str(payload.id),
        status=status,
        order_id=order_id,
        ref_code=ref_code,
        amount=payload.transferAmount,
        raw_payload=payload.model_dump(mode="json"),
        error_message=error_message,
    )
    db.add(event)
    await db.flush()
    return event


async def process_webhook(
    db: AsyncSession, payload: SePayWebhookPayload
) -> WebhookEvent:
    """Idempotently process a SePay webhook payload.

    Always returns a WebhookEvent (caller may inspect ``status``).
    Caller is responsible for committing the session.
    """
    # Outbound transfers can be ignored — we only care about money landing in
    if payload.transferType != "in":
        return await _create_event(
            db, payload, status="unmatched",
            error_message="not an inbound transfer",
        )

    # Idempotency: insert event row first; UNIQUE(provider, sepay_tx_id) blocks dupes
    try:
        event = await _create_event(db, payload, status="received")
    except IntegrityError:
        await db.rollback()
        existing = await db.execute(
            select(WebhookEvent).where(
                WebhookEvent.provider == "sepay",
                WebhookEvent.sepay_tx_id == str(payload.id),
            )
        )
        dup = existing.scalar_one()
        logger.info("sepay webhook duplicate id=%s", payload.id)
        return dup

    # --- Path A: NSQ-XXXXXXXX ref_code → Order fulfillment ---
    ref = parse_ref_code(payload.content) or parse_ref_code(payload.description) or parse_ref_code(payload.referenceCode)
    if ref is not None:
        event.ref_code = ref

        # Lock the order row to prevent concurrent webhook double-fulfill
        result = await db.execute(
            select(Order).where(Order.ref_code == ref).with_for_update()
        )
        order = result.scalar_one_or_none()
        if order is None:
            event.status = "unmatched"
            event.error_message = f"no order for ref_code {ref}"
            return event

        if order.status != "pending":
            # Already paid/cancelled/etc — treat as duplicate
            event.status = "duplicate"
            event.order_id = order.id
            event.error_message = f"order already {order.status}"
            return event

        # Validate amount (allow small over-pay; reject substantial under-pay)
        expected = order.total_amount
        paid = payload.transferAmount
        tolerance = settings.sepay_amount_tolerance_vnd
        if paid + tolerance < expected:
            event.status = "amount_mismatch"
            event.order_id = order.id
            event.error_message = f"paid {paid} < expected {expected}"
            return event

        # Mark order as paid
        order.status = "paid"
        order.paid_at = datetime.now(timezone.utc)
        order.sepay_tx_id = str(payload.id)

        # Fulfillment is delegated to keep this module focused on payments
        from app.services import fulfillment_service  # local import avoids cycle

        try:
            await fulfillment_service.fulfill_order(db, order)
        except Exception as exc:  # noqa: BLE001
            # Order stays paid; we surface a soft error so admin can re-fulfill
            logger.exception("Fulfillment failed for order %s", order.id)
            event.status = "error"
            event.order_id = order.id
            event.error_message = f"fulfillment failed: {exc}"
            return event

        event.status = "matched"
        event.order_id = order.id
        return event

    # --- Path B: CHATADDON<payment_id> → UserPayment / chat addon fulfillment ---
    content_fields = (
        (payload.content or "")
        + " "
        + (payload.description or "")
        + " "
        + (payload.referenceCode or "")
    )
    payment_id = parse_addon_payment_id(content_fields)
    if payment_id is None:
        event.status = "unmatched"
        event.error_message = "no ref_code or CHATADDON marker in content"
        return event

    logger.info("sepay webhook: matched CHATADDON payment_id=%s tx=%s", payment_id, payload.id)

    # Lock the payment row to prevent concurrent double-fulfill
    pay_result = await db.execute(
        select(UserPayment).where(UserPayment.id == payment_id).with_for_update()
    )
    payment = pay_result.scalar_one_or_none()
    if payment is None:
        event.status = "unmatched"
        event.error_message = f"no UserPayment for id={payment_id}"
        return event

    if payment.status != 1:
        # Already approved or rejected — idempotent skip
        event.status = "duplicate"
        event.error_message = f"payment {payment_id} already status={payment.status}"
        return event

    # Validate amount
    paid = payload.transferAmount
    tolerance = settings.sepay_amount_tolerance_vnd
    if paid + tolerance < payment.price:
        event.status = "amount_mismatch"
        event.error_message = f"paid {paid} < expected {payment.price}"
        return event

    # Approve payment — delegates to addon_fulfillment.fulfill_chat_addon
    from app.services.payment_service import approve_payment  # local import avoids cycle

    try:
        await approve_payment(db, payment.id)
    except Exception as exc:  # noqa: BLE001
        logger.exception("approve_payment failed for payment %s", payment.id)
        event.status = "error"
        event.error_message = f"approve_payment failed: {exc}"
        return event

    event.status = "matched"
    return event


# ---------------------------------------------------------------------------
# Reconcile helper — pull recent transactions from SePay API
# ---------------------------------------------------------------------------


async def list_recent_transactions(hours: int = 24) -> list[dict]:
    """Fetch inbound transactions from SePay API for the past `hours`.

    Returns list of dicts: {id, ref_code, amount, transaction_date}.
    Logs only ref_code + amount — never full payload (security).
    Returns [] on API error so the reconcile job degrades gracefully.
    """
    if not settings.sepay_api_key:
        logger.warning("SEPAY_API_KEY not configured; skipping list_recent_transactions")
        return []

    since_dt = datetime.now(timezone.utc) - timedelta(hours=hours)
    # SePay expects Asia/Ho_Chi_Minh local time in YYYY-MM-DD HH:MM:SS format
    since_str = since_dt.strftime("%Y-%m-%d %H:%M:%S")

    params = {
        "limit": 100,
        "transaction_date_min": since_str,
    }
    headers = {"Authorization": f"Bearer {settings.sepay_api_key}"}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(_SEPAY_TX_LIST_URL, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as exc:
        logger.error("SePay API HTTP error %s: %s", exc.response.status_code, exc.response.text[:200])
        return []
    except Exception as exc:  # noqa: BLE001
        logger.error("SePay API request failed: %s", exc)
        return []

    transactions = data.get("transactions") or []
    result = []
    for tx in transactions:
        # Only process inbound transfers
        if tx.get("transfer_type") != "in":
            continue
        ref_code = parse_ref_code(tx.get("transaction_content") or "") or \
                   parse_ref_code(tx.get("reference_number") or "")
        result.append({
            "id": str(tx.get("id", "")),
            "ref_code": ref_code,
            "amount": int(tx.get("amount_in") or tx.get("amount") or 0),
            "transaction_date": tx.get("transaction_date", ""),
        })

    logger.info("SePay list_recent_transactions: fetched %d inbound tx (window=%dh)", len(result), hours)
    return result
