from uuid import UUID
from typing import Dict
from reforma_survey.domain.entities.survey import Survey
from reforma_survey.domain.repositories.survey_repository import SurveyRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class UpdateSurveySettingsUseCase:
    def __init__(self, repository: SurveyRepository):
        self.repository = repository

    async def execute(self, survey_id: UUID, settings: Dict) -> Survey:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.update_settings(survey_id, settings)
                    return updated
                except Exception:
                    raise
