from uuid import UUID

from reforma_survey.domain.entities.branching_rule import BranchingRule
from reforma_survey.domain.repositories.branching_rule_repository import BranchingRuleRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_warning, log_error


class GetBranchingRuleByIdUseCase:
    def __init__(self, repository: BranchingRuleRepository):
        self.repository = repository

    async def execute(self, rule_id: UUID) -> BranchingRule | None:
        log_info(f"Начало получения правила ветвления по ID: {rule_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    rule = await self.repository.get_by_id(rule_id)
                    if rule:
                        log_info(f"Правило ветвления успешно получено: {rule_id}", service="survey-service")
                    else:
                        log_warning(f"Правило ветвления не найдено: {rule_id}", service="survey-service")
                    return rule
                except Exception as e:
                    log_error(f"Ошибка при получении правила ветвления {rule_id}: {e}", service="survey-service")
                    raise