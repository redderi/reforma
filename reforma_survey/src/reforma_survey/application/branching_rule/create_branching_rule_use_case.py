from reforma_survey.domain.entities.branching_rule import BranchingRule
from reforma_survey.domain.repositories.branching_rule_repository import BranchingRuleRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class CreateBranchingRuleUseCase:
    def __init__(self, repository: BranchingRuleRepository):
        self.repository = repository

    async def execute(self, rule: BranchingRule) -> BranchingRule:
        log_info(
            f"Начало создания правила ветвления для вопроса {rule.question_id} "
            f"(ответ: {rule.answer_value}, следующий вопрос: {rule.next_question_id})",
            service="survey-service"
        )

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    created = await self.repository.create(rule)
                    log_info(f"Правило ветвления успешно создано: id={created.id}", service="survey-service")
                    return created
                except Exception as e:
                    log_error(f"Неожиданная ошибка при создании правила ветвления: {e}", service="survey-service")
                    raise