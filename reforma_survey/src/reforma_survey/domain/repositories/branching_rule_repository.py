from abc import ABC, abstractmethod
from typing import List
from uuid import UUID
from reforma_survey.domain.entities.branching_rule import BranchingRule


class BranchingRuleRepository(ABC):
    @abstractmethod
    async def get_by_id(self, rule_id: UUID) -> BranchingRule | None:
        pass

    @abstractmethod
    async def get_by_question(self, question_id: UUID) -> List[BranchingRule]:
        pass

    @abstractmethod
    async def get_default_for_question(self, question_id: UUID) -> BranchingRule | None:
        pass

    @abstractmethod
    async def create(self, rule: BranchingRule) -> BranchingRule:
        pass

    @abstractmethod
    async def update_answer_value(
        self, rule_id: UUID, new_answer_value: str
    ) -> BranchingRule:
        pass

    @abstractmethod
    async def update_next_question(
        self, rule_id: UUID, new_next_question_id: UUID
    ) -> BranchingRule:
        pass

    @abstractmethod
    async def set_default(
        self, rule_id: UUID, is_default: bool = True
    ) -> BranchingRule:
        pass

    @abstractmethod
    async def delete(self, rule_id: UUID) -> None:
        pass

    @abstractmethod
    async def exists(self, rule_id: UUID) -> bool:
        pass

    @abstractmethod
    async def count_by_question(self, question_id: UUID) -> int:
        pass
