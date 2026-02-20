from reforma_survey.domain.entities.branching_rule import BranchingRule
from reforma_survey.domain.repositories.branching_rule_repository import (
    BranchingRuleRepository,
)
from reforma_survey.infrastructure.db.session import SessionLocal


class CreateBranchingRuleUseCase:
    def __init__(self, repository: BranchingRuleRepository):
        self.repository = repository

    async def execute(self, rule: BranchingRule) -> BranchingRule:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    created = await self.repository.create(rule)
                    return created
                except Exception:
                    raise
