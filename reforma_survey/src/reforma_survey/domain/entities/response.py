from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID
from typing import Any, Dict


@dataclass
class Response:
    id: UUID
    survey_id: UUID

    user_id: UUID | None = None
    anonymous_id: str | None = None

    answers: Dict[UUID, Any] = field(
        default_factory=dict
    )  # question_id → ответ (str, int, List[str], etc.)
    submitted_at: datetime | None = None

    ip_address: str | None = None  # IPv4/IPv6 (анонимизированный, например хэш)
    fingerprint: str | None = None  # полный fingerprint от FingerprintJS
    user_agent: str | None = None  # для дополнительной проверки
    device_id: str | None = None  # мобильное приложение
