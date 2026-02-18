from uuid import UUID

from reforma_survey.domain.repositories.branching_rule_repository import BranchingRuleRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info


class BranchingRuleExistsUseCase:
    def __init__(self, repository: BranchingRuleRepository):
        self.repository = repository

    async def execute(self, rule_id: UUID) -> bool:
        log_info(f"Проверка существования правила ветвления {rule_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                exists = await self.repository.exists(rule_id)
                log_info(f"Правило ветвления {rule_id} существует: {exists}", service="survey-service")
                return exists