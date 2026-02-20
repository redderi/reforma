from uuid import UUID
from reforma_survey.domain.entities.branching_rule import BranchingRule
from reforma_survey.domain.repositories.branching_rule_repository import (
    BranchingRuleRepository,
)
from reforma_survey.infrastructure.db.session import SessionLocal


class SetBranchingRuleAsDefaultUseCase:
    def __init__(self, repository: BranchingRuleRepository):
        self.repository = repository

    async def execute(self, rule_id: UUID, is_default: bool = True) -> BranchingRule:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.set_default(rule_id, is_default)
                    return updated
                except Exception:
                    raise
