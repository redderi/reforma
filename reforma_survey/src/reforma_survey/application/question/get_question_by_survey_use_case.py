from typing import List
from uuid import UUID

from reforma_survey.domain.entities.question import Question
from reforma_survey.domain.repositories.question_repository import QuestionRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class GetQuestionsBySurveyUseCase:
    def __init__(self, repository: QuestionRepository):
        self.repository = repository

    async def execute(self, survey_id: UUID) -> List[Question]:
        log_info(f"Начало получения вопросов опроса {survey_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    questions = await self.repository.get_by_survey(survey_id)
                    log_info(f"Получено {len(questions)} вопросов для опроса {survey_id}", service="survey-service")
                    return questions
                except Exception as e:
                    log_error(f"Ошибка получения вопросов опроса {survey_id}: {e}", service="survey-service")
                    raise