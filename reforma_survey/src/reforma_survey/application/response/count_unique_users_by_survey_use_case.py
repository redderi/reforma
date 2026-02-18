from uuid import UUID

from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info


class CountUniqueUsersBySurveyUseCase:
    def __init__(self, repository: ResponseRepository):
        self.repository = repository

    async def execute(self, survey_id: UUID) -> int:
        log_info(f"Подсчёт уникальных респондентов опроса {survey_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                count = await self.repository.count_unique_users_by_survey(survey_id)
                log_info(f"Опрос {survey_id} прошли {count} уникальных пользователей", service="survey-service")
                return count