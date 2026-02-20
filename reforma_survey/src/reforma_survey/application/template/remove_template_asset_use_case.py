from uuid import UUID
from reforma_survey.domain.entities.template import Template
from reforma_survey.domain.repositories.template_repository import TemplateRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class RemoveTemplateAssetUseCase:
    def __init__(self, repository: TemplateRepository):
        self.repository = repository

    async def execute(self, template_id: UUID, asset_url: str) -> Template:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.remove_asset(template_id, asset_url)
                    return updated
                except Exception:
                    raise
