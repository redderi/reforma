from dataclasses import dataclass, field
from uuid import UUID
from typing import Dict, List


@dataclass
class Question:
    id: UUID
    survey_id: UUID
    text: str
    type: str
    options: List[str] = field(default_factory=list)
    style: Dict = field(default_factory=dict)
    order: int = 0
