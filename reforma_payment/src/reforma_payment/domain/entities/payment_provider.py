from dataclasses import dataclass, field
from uuid import UUID, uuid4
from datetime import datetime
from typing import Dict


@dataclass
class PaymentProvider:
    name: str
    provider_type: str
    credentials: Dict[str, str]
    is_active: bool = True

    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
