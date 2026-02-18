from uuid import UUID

from reforma_survey.domain.repositories.branching_rule_repository import BranchingRuleRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info


class CountBranchingRulesByQuestionUseCase:
    def __init__(self, repository: BranchingRuleRepository):
        self.repository = repository

    async def execute(self, question_id: UUID) -> int:
        log_info(f"Подсчёт количества правил ветвления для вопроса {question_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                count = await self.repository.count_by_question(question_id)
                log_info(f"Для вопроса {question_id} найдено {count} правил ветвления", service="survey-service")
                return count