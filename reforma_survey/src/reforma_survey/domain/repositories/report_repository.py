from abc import ABC, abstractmethod
from typing import Optional, List
from reforma_survay.domain.entities.report import Report

class ReportRepository(ABC):

    @abstractmethod
    def get_by_id(self, id: str) -> Optional[Report]:
        pass

    @abstractmethod
    def get_by_user(self, user_id: str) -> List[Report]:
        pass

    @abstractmethod
    def get_by_survey(self, survey_id: str) -> List[Report]:
        pass

    @abstractmethod
    def create(self, report: Report) -> Report:
        pass