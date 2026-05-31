"""Minimal email sender. Falls back to log output if SMTP not configured."""

import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger(__name__)


def _smtp_configured() -> bool:
    return bool(settings.smtp_host)


def send_email(to_email: str, subject: str, body: str) -> None:
    """Send plain-text email via SMTP. Logs payload when SMTP is unset."""
    if not _smtp_configured():
        logger.info(
            "[email:stub] to=%s subject=%s body=\n%s", to_email, subject, body
        )
        return

    msg = EmailMessage()
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)


def send_password_reset_email(to_email: str, raw_token: str) -> None:
    """Send the password-reset link to a user."""
    reset_url = (
        f"{settings.frontend_url.rstrip('/')}"
        f"{settings.password_reset_url_path}?token={raw_token}"
    )
    subject = "Đặt lại mật khẩu Numerology"
    body = (
        "Xin chào,\n\n"
        "Bạn (hoặc ai đó dùng email này) đã yêu cầu đặt lại mật khẩu.\n"
        f"Vui lòng nhấn vào liên kết dưới đây để đặt lại (hết hạn sau "
        f"{settings.password_reset_token_expire_minutes} phút):\n\n"
        f"{reset_url}\n\n"
        "Nếu không phải bạn yêu cầu, vui lòng bỏ qua email này.\n"
    )
    send_email(to_email, subject, body)
