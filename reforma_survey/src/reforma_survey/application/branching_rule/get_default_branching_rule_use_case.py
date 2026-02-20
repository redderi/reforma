from uuid import UUID

from reforma_survey.domain.entities.branching_rule import BranchingRule
from reforma_survey.domain.repositories.branching_rule_repository import (
    BranchingRuleRepository,
)
from reforma_survey.infrastructure.db.session import SessionLocal


class GetDefaultBranchingRuleUseCase:
    def __init__(self, repository: BranchingRuleRepository):
        self.repository = repository

    async def execute(self, question_id: UUID) -> BranchingRule | None:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    rule = await self.repository.get_default_for_question(question_id)
                    return rule
                except Exception:
                    raise
