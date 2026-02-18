from uuid import UUID
from typing import Dict
from reforma_survey.domain.entities.survey import Survey
from reforma_survey.domain.repositories.survey_repository import SurveyRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class UpdateSurveySettingsUseCase:
    def __init__(self, repository: SurveyRepository):
        self.repository = repository

    async def execute(self, survey_id: UUID, settings: Dict) -> Survey:
        log_info(f"Обновление настроек опроса {survey_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.update_settings(survey_id, settings)
                    log_info(f"Настройки опроса {survey_id} обновлены", service="survey-service")
                    return updated
                except Exception as e:
                    log_error(f"Ошибка обновления настроек опроса {survey_id}: {e}", service="survey-service")
                    raise