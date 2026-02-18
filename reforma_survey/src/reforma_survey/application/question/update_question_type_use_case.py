from uuid import UUID
from reforma_survey.domain.entities.question import Question
from reforma_survey.domain.repositories.question_repository import QuestionRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class UpdateQuestionTypeUseCase:
    def __init__(self, repository: QuestionRepository):
        self.repository = repository

    async def execute(self, question_id: UUID, new_type: str) -> Question:
        log_info(f"Обновление типа вопроса {question_id} → {new_type}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.update_type(question_id, new_type)
                    log_info(f"Тип вопроса {question_id} успешно обновлён", service="survey-service")
                    return updated
                except Exception as e:
                    log_error(f"Ошибка обновления типа вопроса {question_id}: {e}", service="survey-service")
                    raise