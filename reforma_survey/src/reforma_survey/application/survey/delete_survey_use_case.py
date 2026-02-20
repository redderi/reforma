from uuid import UUID
from reforma_survey.domain.repositories.survey_repository import SurveyRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class DeleteSurveyUseCase:
    def __init__(self, repository: SurveyRepository):
        self.repository = repository

    async def execute(self, survey_id: UUID) -> None:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    await self.repository.delete(survey_id)
                except Exception:
                    raise
