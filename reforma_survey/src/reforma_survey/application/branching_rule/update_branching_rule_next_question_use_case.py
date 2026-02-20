from uuid import UUID
from reforma_survey.domain.entities.branching_rule import BranchingRule
from reforma_survey.domain.repositories.branching_rule_repository import (
    BranchingRuleRepository,
)
from reforma_survey.infrastructure.db.session import SessionLocal


class UpdateBranchingRuleNextQuestionUseCase:
    def __init__(self, repository: BranchingRuleRepository):
        self.repository = repository

    async def execute(self, rule_id: UUID, new_next_question_id: UUID) -> BranchingRule:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.update_next_question(
                        rule_id, new_next_question_id
                    )
                    return updated
                except Exception:
                    raise
