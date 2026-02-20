from dataclasses import dataclass, field
from uuid import UUID
from typing import List, Dict

from reforma_survey.domain.entities.question import Question


@dataclass
class Survey:
    id: UUID
    owner_id: UUID
    title: str
    description: str | None = None
    settings: Dict = field(default_factory=dict)
    template_id: UUID | None = None

    published: bool = False
    # Вопросы в порядке отображения
    questions: List["Question"] = field(default_factory=list)
