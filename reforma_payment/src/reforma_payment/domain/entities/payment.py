from dataclasses import dataclass, field
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, Dict, Any
from reforma_payment.domain.entities.enums import PaymentStatus


@dataclass
class Payment:
    user_id: UUID
    provider_id: UUID
    amount: int
    currency: str
    idempotency_key: str

    id: UUID = field(default_factory=uuid4)
    status: PaymentStatus = PaymentStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    external_id: Optional[str] = None
    client_secret: Optional[str] = None

    def mark_processing(self, external_id: str, client_secret: str):
        self.status = PaymentStatus.PROCESSING
        self.external_id = external_id
        self.client_secret = client_secret
        self.updated_at = datetime.utcnow()

    def mark_succeeded(self):
        self.status = PaymentStatus.SUCCEEDED
        self.updated_at = datetime.utcnow()

    def mark_failed(self):
        self.status = PaymentStatus.FAILED
        self.updated_at = datetime.utcnow()
