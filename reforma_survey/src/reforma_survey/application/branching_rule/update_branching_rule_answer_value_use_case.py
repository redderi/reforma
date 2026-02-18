from uuid import UUID

from reforma_survey.domain.entities.branching_rule import BranchingRule
from reforma_survey.domain.repositories.branching_rule_repository import BranchingRuleRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class UpdateBranchingRuleAnswerValueUseCase:
    def __init__(self, repository: BranchingRuleRepository):
        self.repository = repository

    async def execute(self, rule_id: UUID, new_answer_value: str) -> BranchingRule:
        log_info(f"Обновление значения ответа в правиле {rule_id} → {new_answer_value}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.update_answer_value(rule_id, new_answer_value)
                    log_info(f"Значение ответа в правиле {rule_id} обновлено", service="survey-service")
                    return updated
                except Exception as e:
                    log_error(f"Ошибка обновления значения ответа в правиле {rule_id}: {e}", service="survey-service")
                    raise