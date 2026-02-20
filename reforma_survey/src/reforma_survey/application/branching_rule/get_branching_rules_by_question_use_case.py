from typing import List
from uuid import UUID

from reforma_survey.domain.entities.branching_rule import BranchingRule
from reforma_survey.domain.repositories.branching_rule_repository import (
    BranchingRuleRepository,
)
from reforma_survey.infrastructure.db.session import SessionLocal


class GetBranchingRulesByQuestionUseCase:
    def __init__(self, repository: BranchingRuleRepository):
        self.repository = repository

    async def execute(self, question_id: UUID) -> List[BranchingRule]:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    rules = await self.repository.get_by_question(question_id)
                    return rules
                except Exception:
                    raise
