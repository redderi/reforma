from uuid import UUID

from reforma_survey.domain.entities.question import Question
from reforma_survey.domain.repositories.question_repository import QuestionRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_warning, log_error


class GetQuestionByIdUseCase:
    def __init__(self, repository: QuestionRepository):
        self.repository = repository

    async def execute(self, question_id: UUID) -> Question | None:
        log_info(f"Начало получения вопроса по ID: {question_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    question = await self.repository.get_by_id(question_id)
                    if question:
                        log_info(f"Вопрос успешно получен: {question_id}", service="survey-service")
                    else:
                        log_warning(f"Вопрос не найден: {question_id}", service="survey-service")
                    return question
                except Exception as e:
                    log_error(f"Ошибка при получении вопроса {question_id}: {e}", service="survey-service")
                    raise