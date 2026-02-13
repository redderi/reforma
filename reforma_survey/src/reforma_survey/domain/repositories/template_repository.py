from abc import ABC, abstractmethod
from typing import Optional, List
from reforma_survay.domain.entities.template import Template

class TemplateRepository(ABC):

    @abstractmethod
    def get_by_id(self, id: str) -> Optional[Template]:
        pass

    @abstractmethod
    def get_by_user(self, user_id: str) -> List[Template]:
        pass

    @abstractmethod
    def create(self, template: Template) -> Template:
        pass

    @abstractmethod
    def update(self, template: Template) -> Template:
        pass

    @abstractmethod
    def delete(self, template: Template) -> None:
        pass