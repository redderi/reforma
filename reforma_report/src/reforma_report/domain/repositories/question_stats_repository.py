from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from reforma_report.domain.entities.question_stats import QuestionStats


class QuestionStatsRepository(ABC):
    @abstractmethod
    async def get(
        self, survey_stat_id: UUID, question_id: UUID
    ) -> Optional[QuestionStats]:
        pass

    @abstractmethod
    async def upsert(self, stats: QuestionStats) -> None:
        pass

    @abstractmethod
    async def list_by_survey(self, survey_stat_id: UUID) -> List[QuestionStats]:
        pass
