from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID
from typing import Any, Dict

@dataclass
class Response:
    id: UUID
    survey_id: UUID
    user_id: UUID
    answers: Dict[UUID, Any] = field(default_factory=dict)  # question_id → ответ (str, int, List[str], etc.)
    submitted_at: datetime | None = None