from reforma_survey.domain.entities.question import Question
from reforma_survey.domain.repositories.question_repository import QuestionRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class CreateQuestionUseCase:
    def __init__(self, repository: QuestionRepository):
        self.repository = repository

    async def execute(self, question: Question) -> Question:
        log_info(f"Начало создания вопроса для опроса {question.survey_id}, text={question.text[:50]}...", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    created = await self.repository.create(question)
                    log_info(f"Вопрос успешно создан: id={created.id}, survey_id={created.survey_id}", service="survey-service")
                    return created
                except Exception as e:
                    log_error(f"Неожиданная ошибка при создании вопроса: {e}", service="survey-service")
                    raise