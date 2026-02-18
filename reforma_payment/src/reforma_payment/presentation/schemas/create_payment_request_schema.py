from typing import Dict
from uuid import UUID
from pydantic import BaseModel


class CreatePaymentRequest(BaseModel):
    user_id: UUID
    amount: int
    currency: str = "RUB"
    idempotency_key: str | None = None
    description: str | None = None
    metadata: Dict[str, str] | None = None
    provider_type: str