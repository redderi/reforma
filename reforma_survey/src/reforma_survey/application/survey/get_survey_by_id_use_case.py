from uuid import UUID
from reforma_survey.domain.entities.survey import Survey
from reforma_survey.domain.repositories.survey_repository import SurveyRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class GetSurveyByIdUseCase:
    def __init__(self, repository: SurveyRepository):
        self.repository = repository

    async def execute(self, survey_id: UUID) -> Survey | None:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    survey = await self.repository.get_by_id(survey_id)
                    return survey
                except Exception:
                    raise
