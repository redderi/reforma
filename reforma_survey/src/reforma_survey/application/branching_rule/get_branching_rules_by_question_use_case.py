from typing import List
from uuid import UUID

from reforma_survey.domain.entities.branching_rule import BranchingRule
from reforma_survey.domain.repositories.branching_rule_repository import BranchingRuleRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class GetBranchingRulesByQuestionUseCase:
    def __init__(self, repository: BranchingRuleRepository):
        self.repository = repository

    async def execute(self, question_id: UUID) -> List[BranchingRule]:
        log_info(f"Начало получения всех правил ветвления для вопроса {question_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    rules = await self.repository.get_by_question(question_id)
                    log_info(f"Получено {len(rules)} правил ветвления для вопроса {question_id}", service="survey-service")
                    return rules
                except Exception as e:
                    log_error(f"Ошибка получения правил ветвления для вопроса {question_id}: {e}", service="survey-service")
                    raise