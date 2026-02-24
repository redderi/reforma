from dataclasses import dataclass, field
from typing import Dict, Optional
from uuid import UUID
from datetime import datetime

@dataclass
class QuestionStats:
    id: UUID
    question_id: UUID
    type: str  

    total: int = 0
    sum: float = 0.0
    sum_of_squares: float = 0.0
    min: Optional[float] = None
    max: Optional[float] = None
    distribution: Dict[str, int] = field(default_factory=dict)

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)