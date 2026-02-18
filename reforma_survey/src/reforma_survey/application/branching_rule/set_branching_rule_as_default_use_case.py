from uuid import UUID

from reforma_survey.domain.entities.branching_rule import BranchingRule
from reforma_survey.domain.repositories.branching_rule_repository import BranchingRuleRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class SetBranchingRuleAsDefaultUseCase:
    def __init__(self, repository: BranchingRuleRepository):
        self.repository = repository

    async def execute(self, rule_id: UUID, is_default: bool = True) -> BranchingRule:
        status = "дефолтным" if is_default else "не дефолтным"
        log_info(f"Установка правила {rule_id} как {status}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.set_default(rule_id, is_default)
                    log_info(f"Правило {rule_id} успешно установлено как {status}", service="survey-service")
                    return updated
                except Exception as e:
                    log_error(f"Ошибка установки дефолтного статуса правила {rule_id}: {e}", service="survey-service")
                    raise