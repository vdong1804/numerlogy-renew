"""Provider implementations for outbound transactional email."""

from app.services.email_providers.base import EmailProvider, EmailSendResult
from app.services.email_providers.smtp_provider import SmtpProvider

__all__ = ["EmailProvider", "EmailSendResult", "SmtpProvider"]
