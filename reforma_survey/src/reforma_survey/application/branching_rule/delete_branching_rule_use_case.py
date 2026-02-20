from uuid import UUID

from reforma_survey.domain.repositories.branching_rule_repository import (
    BranchingRuleRepository,
)
from reforma_survey.infrastructure.db.session import SessionLocal


class DeleteBranchingRuleUseCase:
    def __init__(self, repository: BranchingRuleRepository):
        self.repository = repository

    async def execute(self, rule_id: UUID) -> None:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    await self.repository.delete(rule_id)
                except Exception:
                    raise
