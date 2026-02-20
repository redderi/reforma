from uuid import UUID
from reforma_survey.domain.entities.branching_rule import BranchingRule
from reforma_survey.domain.repositories.branching_rule_repository import (
    BranchingRuleRepository,
)
from reforma_survey.infrastructure.db.session import SessionLocal


class GetBranchingRuleByIdUseCase:
    def __init__(self, repository: BranchingRuleRepository):
        self.repository = repository

    async def execute(self, rule_id: UUID) -> BranchingRule | None:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    rule = await self.repository.get_by_id(rule_id)
                    return rule
                except Exception:
                    raise
