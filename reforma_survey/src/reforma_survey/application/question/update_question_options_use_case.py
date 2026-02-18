from uuid import UUID
from typing import List

from reforma_survey.domain.entities.question import Question
from reforma_survey.domain.repositories.question_repository import QuestionRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class UpdateQuestionOptionsUseCase:
    def __init__(self, repository: QuestionRepository):
        self.repository = repository

    async def execute(self, question_id: UUID, options: List[str]) -> Question:
        log_info(f"Обновление вариантов ответа вопроса {question_id} (кол-во: {len(options)})", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.update_options(question_id, options)
                    log_info(f"Варианты ответа вопроса {question_id} обновлены", service="survey-service")
                    return updated
                except Exception as e:
                    log_error(f"Ошибка обновления вариантов ответа вопроса {question_id}: {e}", service="survey-service")
                    raise