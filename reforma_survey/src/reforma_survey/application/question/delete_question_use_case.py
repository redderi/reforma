from uuid import UUID

from reforma_survey.domain.repositories.question_repository import QuestionRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class DeleteQuestionUseCase:
    def __init__(self, repository: QuestionRepository):
        self.repository = repository

    async def execute(self, question_id: UUID) -> None:
        log_info(f"Начало удаления вопроса {question_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    await self.repository.delete(question_id)
                    log_info(f"Вопрос {question_id} успешно удалён", service="survey-service")
                except Exception as e:
                    log_error(f"Ошибка удаления вопроса {question_id}: {e}", service="survey-service")
                    raise