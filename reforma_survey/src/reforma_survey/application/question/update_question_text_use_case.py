from uuid import UUID

from reforma_survey.domain.entities.question import Question
from reforma_survey.domain.repositories.question_repository import QuestionRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class UpdateQuestionTextUseCase:
    def __init__(self, repository: QuestionRepository):
        self.repository = repository

    async def execute(self, question_id: UUID, new_text: str) -> Question:
        log_info(f"Обновление текста вопроса {question_id} (новый текст: {new_text[:50]}...)", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.update_text(question_id, new_text)
                    log_info(f"Текст вопроса {question_id} успешно обновлён", service="survey-service")
                    return updated
                except Exception as e:
                    log_error(f"Ошибка обновления текста вопроса {question_id}: {e}", service="survey-service")
                    raise