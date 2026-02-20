from uuid import UUID
from reforma_survey.domain.entities.template import Template
from reforma_survey.domain.repositories.template_repository import TemplateRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class UpdateTemplateNameUseCase:
    def __init__(self, repository: TemplateRepository):
        self.repository = repository

    async def execute(self, template_id: UUID, new_name: str) -> Template:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.update_name(template_id, new_name)
                    return updated
                except ValueError:
                    raise
                except Exception:
                    raise
