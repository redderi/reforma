from typing import List
from uuid import UUID

from reforma_survey.domain.entities.survey import Survey
from reforma_survey.domain.repositories.survey_repository import SurveyRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class GetSurveysByOwnerUseCase:
    def __init__(self, repository: SurveyRepository):
        self.repository = repository

    async def execute(self, owner_id: UUID) -> List[Survey]:
        log_info(f"Начало получения опросов владельца: {owner_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    surveys = await self.repository.get_by_owner(owner_id)
                    log_info(f"Получено {len(surveys)} опросов для владельца {owner_id}", service="survey-service")
                    return surveys
                except Exception as e:
                    log_error(f"Ошибка получения опросов владельца {owner_id}: {e}", service="survey-service")
                    raise