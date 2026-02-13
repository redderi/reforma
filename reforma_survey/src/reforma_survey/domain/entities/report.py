from dataclasses import dataclass, field
from uuid import UUID
from typing import Dict, List

@dataclass
class Report:
    id: UUID
    survey_id: UUID
    owner_id: UUID
    created_at: str
    summary: Dict = field(default_factory=dict)       # аналитика, например {'question_id': {'option': count}}
    charts: List[str] = field(default_factory=list)  # ссылки на сгенерированные графики/отчёты