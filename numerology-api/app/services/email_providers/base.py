"""Email provider abstract — SMTP implements this; future providers can plug in here."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class EmailSendResult:
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class EmailProvider(ABC):
    @abstractmethod
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
        """Send a single email; return success flag + provider id or error."""
        raise NotImplementedError
