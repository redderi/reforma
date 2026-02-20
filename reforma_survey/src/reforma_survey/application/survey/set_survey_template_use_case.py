from uuid import UUID
from reforma_survey.domain.entities.survey import Survey
from reforma_survey.domain.repositories.survey_repository import SurveyRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class SetSurveyTemplateUseCase:
    def __init__(self, repository: SurveyRepository):
        self.repository = repository

    async def execute(self, survey_id: UUID, template_id: UUID | None) -> Survey:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.set_template(survey_id, template_id)
                    return updated
                except Exception:
                    raise
