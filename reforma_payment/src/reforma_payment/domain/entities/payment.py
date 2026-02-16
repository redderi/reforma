from dataclasses import dataclass, field
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, Dict


@dataclass
class Payment:
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    provider_id: Optional[UUID] = None  
    amount: int = 0  # в центах/копейках
    currency: str = "USD"
    status: str = "pending"  # pending, success, failed
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict = field(default_factory=dict)  # дополнительные данные
    description: Optional[str] = None
    idempotency_key: Optional[str] = None
