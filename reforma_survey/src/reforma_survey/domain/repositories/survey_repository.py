from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from reforma_survey.domain.entities.survey import Survey


class SurveyRepository(ABC):

    @abstractmethod
    async def get_by_id(self, survey_id: UUID) -> Survey | None:
        pass

    @abstractmethod
    async def get_by_owner(self, owner_id: UUID) -> List[Survey]:
        pass

    @abstractmethod
    async def get_published_by_owner(self, owner_id: UUID) -> List[Survey]:
        pass

    @abstractmethod
    async def get_published(self) -> List[Survey]:
        pass

    @abstractmethod
    async def create(self, survey: Survey) -> Survey:
        pass

    @abstractmethod
    async def update_title(self, survey_id: UUID, new_title: str) -> Survey:
        pass

    @abstractmethod
    async def update_description(self, survey_id: UUID, description: str | None) -> Survey:
        pass

    @abstractmethod
    async def update_settings(self, survey_id: UUID, settings: dict) -> Survey:
        pass

    @abstractmethod
    async def set_template(self, survey_id: UUID, template_id: UUID | None) -> Survey:
        pass

    @abstractmethod
    async def publish(self, survey_id: UUID) -> Survey:
        pass

    @abstractmethod
    async def unpublish(self, survey_id: UUID) -> Survey:
        pass

    @abstractmethod
    async def delete(self, survey_id: UUID) -> None:
        pass

    @abstractmethod
    async def add_question(self, survey_id: UUID, question_id: UUID) -> Survey:
        pass

    @abstractmethod
    async def remove_question(self, survey_id: UUID, question_id: UUID) -> Survey:
        pass

    @abstractmethod
    async def reorder_questions(
        self,
        survey_id: UUID,
        question_ids: List[UUID]
    ) -> Survey:
        pass

    @abstractmethod
    async def exists(self, survey_id: UUID) -> bool:
        pass

    @abstractmethod
    async def count_by_owner(self, owner_id: UUID) -> int:
        pass