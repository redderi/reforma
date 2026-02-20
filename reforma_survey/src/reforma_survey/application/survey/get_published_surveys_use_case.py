from typing import List
from uuid import UUID
from reforma_survey.domain.entities.survey import Survey
from reforma_survey.domain.repositories.survey_repository import SurveyRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class GetPublishedSurveysUseCase:
    def __init__(self, repository: SurveyRepository):
        self.repository = repository

    async def execute(self, owner_id: UUID | None = None) -> List[Survey]:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    surveys = await self.repository.get_published(owner_id)
                    return surveys
                except Exception:
                    raise
