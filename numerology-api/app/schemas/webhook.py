"""Pydantic schemas for inbound webhooks (SePay et al.)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SePayWebhookPayload(BaseModel):
    """SePay v2 webhook payload.

    See https://docs.sepay.vn/ — field names align with SePay's documented schema.
    Unknown fields are ignored so a SePay schema bump doesn't break us.
    """

    model_config = ConfigDict(extra="ignore")

    id: int  # SePay transaction id (idempotency key)
    gateway: Optional[str] = None
    transactionDate: Optional[datetime] = Field(default=None)
    accountNumber: Optional[str] = None
    code: Optional[str] = None
    content: str = ""
    transferType: str = "in"  # 'in' for credit, 'out' for debit
    transferAmount: int = 0  # VND
    referenceCode: Optional[str] = None
    description: Optional[str] = None
