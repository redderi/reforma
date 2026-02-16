from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

@dataclass
class IdempotencyKey:
    key: str
    payment_id: UUID
    created_at: datetime = field(default_factory=datetime.utcnow)