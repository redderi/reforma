from dataclasses import dataclass
from uuid import UUID

@dataclass
class BranchingRule:
    id: UUID
    question_id: UUID
    answer_value: str                   # конкретный ответ ("Да", "5", "blue")
    next_question_id: UUID              # следующий вопрос
    is_default: bool = False            # fallback-правило