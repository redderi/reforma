from uuid import UUID
from typing import Dict
from reforma_survey.domain.entities.template import Template
from reforma_survey.domain.repositories.template_repository import TemplateRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class UpdateTemplateSurveyStyleUseCase:
    def __init__(self, repository: TemplateRepository):
        self.repository = repository

    async def execute(self, template_id: UUID, survey_style: Dict) -> Template:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.update_survey_style(
                        template_id, survey_style
                    )
                    return updated
                except Exception:
                    raise
