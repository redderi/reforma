from uuid import UUID

from reforma_survey.domain.entities.branching_rule import BranchingRule
from reforma_survey.domain.repositories.branching_rule_repository import (
    BranchingRuleRepository,
)
from reforma_survey.infrastructure.db.session import SessionLocal


class UpdateBranchingRuleAnswerValueUseCase:
    def __init__(self, repository: BranchingRuleRepository):
        self.repository = repository

    async def execute(self, rule_id: UUID, new_answer_value: str) -> BranchingRule:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.update_answer_value(
                        rule_id, new_answer_value
                    )
                    return updated
                except Exception:
                    raise
