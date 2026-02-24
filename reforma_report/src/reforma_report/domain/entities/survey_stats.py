from dataclasses import dataclass, field
from typing import Dict, Optional, List
from uuid import UUID, uuid4
from datetime import datetime

@dataclass
class SurveyStats:
    id: UUID
    survey_id: UUID
    owner_id: UUID
    allowed_user_ids: list[UUID] = field(default_factory=list)

    total_responses: int = 0

    # Агрегаты по типам вопросов
    sum_per_type: Dict[str, float] = field(default_factory=dict)
    sum_of_squares_per_type: Dict[str, float] = field(default_factory=dict)
    min_per_type: Dict[str, Optional[float]] = field(default_factory=dict)
    max_per_type: Dict[str, Optional[float]] = field(default_factory=dict)

    # Поля для хранения результатов ИИ
    sentiment_summary: Optional[Dict[str, float]] = None
    keyword_analysis: Optional[Dict[str, int]] = None
    recommendations: Optional[list[str]] = field(default_factory=list)

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)