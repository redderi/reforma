from uuid import UUID

from reforma_survey.domain.entities.question import Question
from reforma_survey.domain.repositories.question_repository import QuestionRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class UpdateQuestionOrderUseCase:
    def __init__(self, repository: QuestionRepository):
        self.repository = repository

    async def execute(self, question_id: UUID, new_order: int) -> Question:
        log_info(f"Обновление порядка вопроса {question_id} → {new_order}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.update_order(question_id, new_order)
                    log_info(f"Порядок вопроса {question_id} обновлён на {new_order}", service="survey-service")
                    return updated
                except Exception as e:
                    log_error(f"Ошибка обновления порядка вопроса {question_id}: {e}", service="survey-service")
                    raise