from abc import ABC, abstractmethod
from typing import Optional, List
from reforma_survay.domain.entities.response import Response

class ResponseRepository(ABC):

    @abstractmethod
    def get_by_id(self, id: str) -> Optional[Response]:
        pass

    @abstractmethod
    def get_by_survey(self, survey_id: str) -> List[Response]:
        pass

    @abstractmethod
    def get_by_user(self, user_id: str) -> List[Response]:
        pass

    @abstractmethod
    def create(self, response: Response) -> Response:
        pass