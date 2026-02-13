from abc import ABC, abstractmethod
from typing import Optional, List
from reforma_survay.domain.entities.branching_rule import BranchingRule

class BranchingRuleRepository(ABC):

    @abstractmethod
    def get_by_id(self, id: str) -> Optional[BranchingRule]:
        pass

    @abstractmethod
    def get_by_question(self, question_id: str) -> List[BranchingRule]:
        pass

    @abstractmethod
    def create(self, rule: BranchingRule) -> BranchingRule:
        pass

    @abstractmethod
    def delete(self, rule: BranchingRule) -> None:
        pass