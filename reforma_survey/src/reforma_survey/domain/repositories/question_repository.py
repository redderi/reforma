from abc import ABC, abstractmethod
from typing import Dict, List
from uuid import UUID

from reforma_survey.domain.entities.question import Question


class QuestionRepository(ABC):

    @abstractmethod
    async def get_by_id(self, question_id: UUID) -> Question | None:
        pass

    @abstractmethod
    async def get_by_survey(self, survey_id: UUID) -> List[Question]:
        pass

    @abstractmethod
    async def get_by_survey_ordered(self, survey_id: UUID) -> List[Question]:
        pass

    @abstractmethod
    async def create(self, question: Question) -> Question:
        pass

    @abstractmethod
    async def update_text(self, question_id: UUID, new_text: str) -> Question:
        pass

    @abstractmethod
    async def update_type(self, question_id: UUID, new_type: str) -> Question:
        pass

    @abstractmethod
    async def update_options(self, question_id: UUID, options: List[str]) -> Question:
        pass

    @abstractmethod
    async def update_style(self, question_id: UUID, style: Dict) -> Question:
        pass

    @abstractmethod
    async def update_order(self, question_id: UUID, new_order: int) -> Question:
        pass

    @abstractmethod
    async def delete(self, question_id: UUID) -> None:
        pass

    @abstractmethod
    async def exists(self, question_id: UUID) -> bool:
        pass

    @abstractmethod
    async def count_by_survey(self, survey_id: UUID) -> int:
        pass