from uuid import UUID

from reforma_survey.domain.repositories.question_repository import QuestionRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info


class CountQuestionsBySurveyUseCase:
    def __init__(self, repository: QuestionRepository):
        self.repository = repository

    async def execute(self, survey_id: UUID) -> int:
        log_info(f"Подсчёт количества вопросов в опросе {survey_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                count = await self.repository.count_by_survey(survey_id)
                log_info(f"В опросе {survey_id} найдено {count} вопросов", service="survey-service")
                return count