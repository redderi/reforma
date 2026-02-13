# domain/entities/branch.py
from dataclasses import dataclass
from uuid import UUID
from typing import Dict

@dataclass
class BranchingRule:
    question_id: UUID
    conditions: Dict[str, UUID]  # 'answer_value' -> 'next_question_id'