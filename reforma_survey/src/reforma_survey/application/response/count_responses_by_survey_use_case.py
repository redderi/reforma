from uuid import UUID

from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info


class CountResponsesBySurveyUseCase:
    def __init__(self, repository: ResponseRepository):
        self.repository = repository

    async def execute(self, survey_id: UUID) -> int:
        log_info(f"Подсчёт ответов на опрос {survey_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                count = await self.repository.count_by_survey(survey_id)
                log_info(f"На опросе {survey_id} найдено {count} ответов", service="survey-service")
                return count