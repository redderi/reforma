from dataclasses import dataclass, field
from uuid import UUID
from typing import Dict, List


@dataclass
class Template:
    id: UUID
    owner_id: UUID
    name: str
    description: str | None = None
    survey_style: Dict = field(default_factory=dict)  # стили для всего опроса
    question_style: Dict = field(default_factory=dict)  # базовые стили вопросов
    assets: List[str] = field(default_factory=list)  # логотипы, картинки
