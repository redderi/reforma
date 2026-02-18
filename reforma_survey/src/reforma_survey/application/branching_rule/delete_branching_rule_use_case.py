from uuid import UUID

from reforma_survey.domain.repositories.branching_rule_repository import BranchingRuleRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class DeleteBranchingRuleUseCase:
    def __init__(self, repository: BranchingRuleRepository):
        self.repository = repository

    async def execute(self, rule_id: UUID) -> None:
        log_info(f"Начало удаления правила ветвления {rule_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    await self.repository.delete(rule_id)
                    log_info(f"Правило ветвления {rule_id} успешно удалено", service="survey-service")
                except Exception as e:
                    log_error(f"Ошибка удаления правила ветвления {rule_id}: {e}", service="survey-service")
                    raise