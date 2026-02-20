from uuid import UUID
from reforma_survey.domain.repositories.template_repository import TemplateRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class DeleteTemplateUseCase:
    def __init__(self, repository: TemplateRepository):
        self.repository = repository

    async def execute(self, template_id: UUID) -> None:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    await self.repository.delete(template_id)
                except Exception:
                    raise
