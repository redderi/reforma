# reforma_survey/application/use_cases/branching_rule/update_branching_rule_next_question.py

from uuid import UUID

from reforma_survey.domain.entities.branching_rule import BranchingRule
from reforma_survey.domain.repositories.branching_rule_repository import BranchingRuleRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class UpdateBranchingRuleNextQuestionUseCase:
    def __init__(self, repository: BranchingRuleRepository):
        self.repository = repository

    async def execute(self, rule_id: UUID, new_next_question_id: UUID) -> BranchingRule:
        log_info(f"Обновление следующего вопроса в правиле {rule_id} → {new_next_question_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.update_next_question(rule_id, new_next_question_id)
                    log_info(f"Следующий вопрос в правиле {rule_id} обновлён", service="survey-service")
                    return updated
                except Exception as e:
                    log_error(f"Ошибка обновления следующего вопроса в правиле {rule_id}: {e}", service="survey-service")
                    raise