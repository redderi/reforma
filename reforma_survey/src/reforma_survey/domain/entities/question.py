from dataclasses import dataclass, field
from uuid import UUID
from typing import Dict, List

@dataclass
class Question:
    id: UUID
    survey_id: UUID
    text: str
    type: str                           # single_choice, multiple_choice, text, slider, rating, date и т.д.
    options: List[str] = field(default_factory=list)
    style: Dict = field(default_factory=dict)
    order: int = 0                      # ← позиция в опросе (0, 1, 2...)

    next_questions: Dict[str, UUID] = field(default_factory=dict)
    # Пример:
    # {
    #     "Да": UUID(...),           # если выбрали "Да" → вопрос 5
    #     "Нет": UUID(...),
    #     "default": UUID(...)       # если ничего не подошло
    # }