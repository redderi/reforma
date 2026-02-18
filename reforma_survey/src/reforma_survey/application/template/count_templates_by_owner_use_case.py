from uuid import UUID

from reforma_survey.domain.repositories.template_repository import TemplateRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info


class CountTemplatesByOwnerUseCase:
    def __init__(self, repository: TemplateRepository):
        self.repository = repository

    async def execute(self, owner_id: UUID) -> int:
        log_info(f"Подсчёт количества шаблонов у владельца {owner_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                count = await self.repository.count_by_owner(owner_id)
                log_info(f"У владельца {owner_id} найдено {count} шаблонов", service="survey-service")
                return count