from typing import List
from uuid import UUID
from reforma_survey.domain.entities.template import Template
from reforma_survey.domain.repositories.template_repository import TemplateRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class GetTemplatesByOwnerUseCase:
    def __init__(self, repository: TemplateRepository):
        self.repository = repository

    async def execute(self, owner_id: UUID) -> List[Template]:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    templates = await self.repository.get_by_owner(owner_id)
                    return templates
                except Exception:
                    raise
