from dataclasses import dataclass, field
from uuid import UUID
from typing import Dict

@dataclass
class Response:
    id: UUID
    survey_id: UUID
    user_id: UUID
    answers: Dict[UUID, str] = field(default_factory=dict) # question_id -> answer
    submitted_at: str | None = None