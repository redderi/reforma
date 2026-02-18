from uuid import UUID

from reforma_survey.domain.repositories.survey_repository import SurveyRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info


class SurveyExistsUseCase:
    def __init__(self, repository: SurveyRepository):
        self.repository = repository

    async def execute(self, survey_id: UUID) -> bool:
        log_info(f"Проверка существования опроса {survey_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                exists = await self.repository.exists(survey_id)
                log_info(f"Опрос {survey_id} существует: {exists}", service="survey-service")
                return exists