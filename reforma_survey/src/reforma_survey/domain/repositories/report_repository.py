from abc import ABC, abstractmethod
from typing import List
from uuid import UUID
from datetime import datetime

from reforma_survey.domain.entities.report import Report


class ReportRepository(ABC):

    @abstractmethod
    async def get_by_id(self, report_id: UUID) -> Report | None:
        pass

    @abstractmethod
    async def get_by_survey(self, survey_id: UUID) -> Report | None:
        pass

    @abstractmethod
    async def get_by_owner(self, owner_id: UUID) -> List[Report]:
        pass

    @abstractmethod
    async def get_latest_by_survey(self, survey_id: UUID) -> Report | None:
        pass

    @abstractmethod
    async def create(self, report: Report) -> Report:
        pass

    @abstractmethod
    async def update_status(
        self,
        report_id: UUID,
        new_status: str,
        processing_started_at: datetime | None = None,
        completed_at: datetime | None = None,
        error_message: str | None = None
    ) -> Report:
        pass

    @abstractmethod
    async def add_file_url(self, report_id: UUID, file_url: str) -> Report:
        pass

    @abstractmethod
    async def set_file_urls(self, report_id: UUID, file_urls: List[str]) -> Report:
        pass


    @abstractmethod
    async def delete(self, report_id: UUID) -> None:
        pass

    @abstractmethod
    async def exists(self, report_id: UUID) -> bool:
        pass

    @abstractmethod
    async def count_by_survey(self, survey_id: UUID) -> int:
        pass

    @abstractmethod
    async def count_by_owner(self, owner_id: UUID) -> int:
        pass