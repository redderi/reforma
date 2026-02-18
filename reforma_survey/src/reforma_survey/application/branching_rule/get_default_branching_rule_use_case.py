from uuid import UUID

from reforma_survey.domain.entities.branching_rule import BranchingRule
from reforma_survey.domain.repositories.branching_rule_repository import BranchingRuleRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_warning, log_error


class GetDefaultBranchingRuleUseCase:
    def __init__(self, repository: BranchingRuleRepository):
        self.repository = repository

    async def execute(self, question_id: UUID) -> BranchingRule | None:
        log_info(f"Получение дефолтного правила ветвления для вопроса {question_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    rule = await self.repository.get_default_for_question(question_id)
                    if rule:
                        log_info(f"Дефолтное правило найдено для вопроса {question_id}", service="survey-service")
                    else:
                        log_warning(f"Дефолтное правило не найдено для вопроса {question_id}", service="survey-service")
                    return rule
                except Exception as e:
                    log_error(f"Ошибка получения дефолтного правила для вопроса {question_id}: {e}", service="survey-service")
                    raise