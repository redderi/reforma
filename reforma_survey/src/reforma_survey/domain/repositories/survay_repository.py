from abc import ABC, abstractmethod
from typing import Optional, List
from reforma_survay.domain.entities.survay import Survey

class SurveyRepository(ABC):

    @abstractmethod
    def get_by_id(self, id: str) -> Optional[Survey]:
        pass

    @abstractmethod
    def get_by_user(self, user_id: str) -> List[Survey]:
        pass

    @abstractmethod
    def create(self, survey: Survey) -> Survey:
        pass

    @abstractmethod
    def update(self, survey: Survey) -> Survey:
        pass

    @abstractmethod
    def delete(self, survey: Survey) -> None:
        pass