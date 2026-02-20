from uuid import UUID
from reforma_survey.domain.repositories.survey_repository import SurveyRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class SurveyExistsUseCase:
    def __init__(self, repository: SurveyRepository):
        self.repository = repository

    async def execute(self, survey_id: UUID) -> bool:
        async with SessionLocal() as db:
            async with db.begin():
                exists = await self.repository.exists(survey_id)
                return exists
