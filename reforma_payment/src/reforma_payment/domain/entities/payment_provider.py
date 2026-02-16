
from dataclasses import dataclass, field
from uuid import UUID, uuid4
from typing import Dict


@dataclass
class PaymentProvider:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    is_active: bool = True
    config: Dict = field(default_factory=dict)  # API keys, secrets, etc.