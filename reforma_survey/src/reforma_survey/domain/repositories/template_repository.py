from abc import ABC, abstractmethod
from typing import Dict, List
from uuid import UUID
from reforma_survey.domain.entities.template import Template


class TemplateRepository(ABC):
    @abstractmethod
    async def get_by_id(self, template_id: UUID) -> Template | None:
        pass

    @abstractmethod
    async def get_by_owner(self, owner_id: UUID) -> List[Template]:
        pass

    @abstractmethod
    async def get_by_name(self, owner_id: UUID, name: str) -> Template | None:
        pass

    @abstractmethod
    async def create(self, template: Template) -> Template:
        pass

    @abstractmethod
    async def update_name(self, template_id: UUID, new_name: str) -> Template:
        pass

    @abstractmethod
    async def update_description(
        self, template_id: UUID, description: str | None
    ) -> Template:
        pass

    @abstractmethod
    async def update_survey_style(
        self, template_id: UUID, survey_style: Dict
    ) -> Template:
        pass

    @abstractmethod
    async def update_question_style(
        self, template_id: UUID, question_style: Dict
    ) -> Template:
        pass

    @abstractmethod
    async def add_asset(self, template_id: UUID, asset_url: str) -> Template:
        pass

    @abstractmethod
    async def remove_asset(self, template_id: UUID, asset_url: str) -> Template:
        pass

    @abstractmethod
    async def delete(self, template_id: UUID) -> None:
        pass

    @abstractmethod
    async def exists(self, template_id: UUID) -> bool:
        pass

    @abstractmethod
    async def count_by_owner(self, owner_id: UUID) -> int:
        pass
