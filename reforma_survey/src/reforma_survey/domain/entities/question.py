from dataclasses import dataclass, field
from uuid import UUID
from typing import Dict, List

@dataclass
class Question:
    id: UUID
    survey_id: UUID
    text: str
    type: str                                       # single_choice, multiple_choice, slider, text, rating
    options: List[str] = field(default_factory=list) # варианты ответа (для choice)
    style: Dict = field(default_factory=dict)       # индивидуальные стили (цвета, кнопки, фон)
    branching_logic: Dict = field(default_factory=dict) # {'next_question_id': condition}