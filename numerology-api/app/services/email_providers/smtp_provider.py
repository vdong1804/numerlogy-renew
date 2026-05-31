"""SMTP fallback provider."""

import logging
import smtplib
from email.message import EmailMessage
from typing import Optional

from app.config import settings
from app.services.email_providers.base import EmailProvider, EmailSendResult

logger = logging.getLogger(__name__)


class SmtpProvider(EmailProvider):
    async def send(
        self,
        *,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None,
        from_address: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> EmailSendResult:
        if not settings.smtp_host:
            logger.info("[email:smtp-stub] to=%s subject=%s (no host)", to, subject)
            return EmailSendResult(success=True, message_id="stub-no-smtp")
        try:
            msg = EmailMessage()
            msg["From"] = from_address or settings.smtp_from
            msg["To"] = to
            msg["Subject"] = subject
            if reply_to:
                msg["Reply-To"] = reply_to
            msg.set_content(text or _html_to_text(html))
            msg.add_alternative(html, subtype="html")

            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
                if settings.smtp_use_tls:
                    smtp.starttls()
                if settings.smtp_user:
                    smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(msg)
            return EmailSendResult(success=True, message_id=msg["Message-ID"])
        except Exception as exc:  # noqa: BLE001
            return EmailSendResult(success=False, error=str(exc))


def _html_to_text(html: str) -> str:
    """Very rough HTML stripping for plain-text fallback. Good enough for emails."""
    import re

    no_tags = re.sub(r"<[^>]+>", "", html)
    return re.sub(r"\s+", " ", no_tags).strip()
