from uuid import UUID
from typing import Dict

from reforma_survey.domain.entities.question import Question
from reforma_survey.domain.repositories.question_repository import QuestionRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class UpdateQuestionStyleUseCase:
    def __init__(self, repository: QuestionRepository):
        self.repository = repository

    async def execute(self, question_id: UUID, style: Dict) -> Question:
        log_info(f"Обновление стиля вопроса {question_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.update_style(question_id, style)
                    log_info(f"Стиль вопроса {question_id} успешно обновлён", service="survey-service")
                    return updated
                except Exception as e:
                    log_error(f"Ошибка обновления стиля вопроса {question_id}: {e}", service="survey-service")
                    raise