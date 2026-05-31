"""Outbox-style email service.

Public API:
    enqueue(...)       — insert a pending row (caller commits)
    dispatch_batch(...) — claim + send up to N pending rows
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models.email_outbox import EmailOutbox
from app.services.email_providers import EmailProvider, SmtpProvider

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "emails"

# HTML env with autoescaping; plain-text env without (preserves whitespace/chars)
_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)
_jinja_txt_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=False,
)

# Backoff schedule in minutes
_BACKOFF_MINUTES = [1, 5, 15, 60, 360]
_MAX_ATTEMPTS = len(_BACKOFF_MINUTES)


def _next_retry_at(attempts: int) -> datetime:
    idx = min(attempts, _MAX_ATTEMPTS - 1)
    return datetime.now(timezone.utc) + timedelta(minutes=_BACKOFF_MINUTES[idx])


def _select_provider() -> EmailProvider:
    """SMTP is the only provider in use."""
    return SmtpProvider()


def _enrich_payload(payload: dict) -> dict:
    """Inject frontend_url so all templates can render unsubscribe + links."""
    enriched = dict(payload)
    enriched.setdefault("frontend_url", settings.frontend_url)
    return enriched


def render_template(template: str, payload: dict) -> tuple[str, str]:
    """Return (subject, html). Subject is the first `<title>` content."""
    import re

    enriched = _enrich_payload(payload)
    tpl = _jinja_env.get_template(f"{template}.html")
    html = tpl.render(**enriched)

    # Best-effort subject extraction from <title>...</title>
    m = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    subject = (m.group(1).strip() if m else payload.get("subject") or template)
    return subject, html


def render_text_template(template: str, payload: dict) -> Optional[str]:
    """Return plain-text body if a .txt sibling exists, else None."""
    enriched = _enrich_payload(payload)
    try:
        tpl = _jinja_txt_env.get_template(f"{template}.txt")
        return tpl.render(**enriched)
    except Exception:  # noqa: BLE001
        return None


async def enqueue(
    db: AsyncSession,
    *,
    to_email: str,
    template: str,
    payload: Optional[dict] = None,
    user_id: Optional[int] = None,
) -> EmailOutbox:
    """Insert a pending email_outbox row. Caller must commit the session."""
    payload = payload or {}
    subject, _ = render_template(template, payload)
    row = EmailOutbox(
        user_id=user_id,
        to_email=to_email,
        template=template,
        subject=subject,
        payload=payload,
        status="pending",
        attempts=0,
    )
    db.add(row)
    await db.flush()
    return row


async def dispatch_batch(db: AsyncSession, limit: int = 50) -> dict:
    """Send up to `limit` pending emails. Returns counters."""
    provider = _select_provider()
    now = datetime.now(timezone.utc)

    stmt = (
        select(EmailOutbox)
        .where(
            EmailOutbox.status == "pending",
            (EmailOutbox.next_retry_at.is_(None)) | (EmailOutbox.next_retry_at <= now),
        )
        .order_by(EmailOutbox.id)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    rows = (await db.execute(stmt)).scalars().all()

    sent = failed = retried = 0
    for row in rows:
        try:
            _, html = render_template(row.template, row.payload or {})
        except Exception as exc:  # noqa: BLE001
            row.status = "failed"
            row.error_message = f"template error: {exc}"
            failed += 1
            continue

        # Render plain-text sibling for multipart/alternative (better deliverability)
        text = render_text_template(row.template, row.payload or {})

        result = await provider.send(
            to=row.to_email,
            subject=row.subject,
            html=html,
            text=text,
        )
        row.attempts = (row.attempts or 0) + 1
        if result.success:
            row.status = "sent"
            row.provider_message_id = result.message_id
            row.sent_at = datetime.now(timezone.utc)
            row.error_message = None
            sent += 1
        elif row.attempts >= _MAX_ATTEMPTS:
            row.status = "failed"
            row.error_message = result.error
            failed += 1
        else:
            row.next_retry_at = _next_retry_at(row.attempts)
            row.error_message = result.error
            retried += 1

    await db.flush()
    return {"sent": sent, "failed": failed, "retried": retried, "claimed": len(rows)}
