from abc import ABC, abstractmethod
from typing import Optional, List
from reforma_survay.domain.entities.question import Question

class QuestionRepository(ABC):

    @abstractmethod
    def get_by_id(self, id: str) -> Optional[Question]:
        pass

    @abstractmethod
    def get_by_survey(self, survey_id: str) -> List[Question]:
        pass

    @abstractmethod
    def create(self, question: Question) -> Question:
        pass

    @abstractmethod
    def update(self, question: Question) -> Question:
        pass

    @abstractmethod
    def delete(self, question: Question) -> None:
        pass