from uuid import UUID
from reforma_survey.domain.entities.template import Template
from reforma_survey.domain.repositories.template_repository import TemplateRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class GetTemplateByIdUseCase:
    def __init__(self, repository: TemplateRepository):
        self.repository = repository

    async def execute(self, template_id: UUID) -> Template | None:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    template = await self.repository.get_by_id(template_id)
                    return template
                except Exception:
                    raise
