from abc import ABC, abstractmethod
from uuid import UUID
from typing import Optional
from reforma_report.domain.entities.survey_stats import SurveyStats


class SurveyStatsRepository(ABC):
    @abstractmethod
    async def get(self, survey_id: UUID) -> Optional[SurveyStats]:
        pass

    @abstractmethod
    async def create(self, survey_stats: SurveyStats) -> None:
        pass

    @abstractmethod
    async def update(self, survey_stats: SurveyStats) -> None:
        pass

    @abstractmethod
    async def add_allowed_user(self, survey_id: UUID, user_id: UUID) -> None:
        pass

    @abstractmethod
    async def remove_allowed_user(self, survey_id: UUID, user_id: UUID) -> None:
        pass

    @abstractmethod
    async def user_has_access(self, survey_id: UUID, user_id: UUID) -> bool:
        pass
