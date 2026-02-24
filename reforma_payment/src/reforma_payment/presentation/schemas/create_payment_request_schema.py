from typing import Dict
from uuid import UUID
from pydantic import BaseModel


class CreatePaymentRequest(BaseModel):
    amount: int
    currency: str = "rub"
    provider_type: str = "stripe"
    user_id: UUID
    idempotency_key: str
    description: str | None = None
    payment_metadata: dict | None = None
    return_url: str | None = None          # ← добавь это поле!