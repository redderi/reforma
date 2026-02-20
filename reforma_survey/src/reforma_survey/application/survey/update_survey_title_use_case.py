from uuid import UUID
from reforma_survey.domain.entities.survey import Survey
from reforma_survey.domain.repositories.survey_repository import SurveyRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class UpdateSurveyTitleUseCase:
    def __init__(self, repository: SurveyRepository):
        self.repository = repository

    async def execute(self, survey_id: UUID, new_title: str) -> Survey:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.update_title(survey_id, new_title)
                    return updated
                except ValueError:
                    raise
                except Exception:
                    raise
