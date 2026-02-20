from uuid import UUID
from reforma_survey.domain.repositories.template_repository import TemplateRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class TemplateExistsUseCase:
    def __init__(self, repository: TemplateRepository):
        self.repository = repository

    async def execute(self, template_id: UUID) -> bool:
        async with SessionLocal() as db:
            async with db.begin():
                exists = await self.repository.exists(template_id)
                return exists
