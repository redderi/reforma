from typing import List
from uuid import UUID

from reforma_survey.domain.entities.template import Template
from reforma_survey.domain.repositories.template_repository import TemplateRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class GetTemplatesByOwnerUseCase:
    def __init__(self, repository: TemplateRepository):
        self.repository = repository

    async def execute(self, owner_id: UUID) -> List[Template]:
        log_info(f"Начало получения шаблонов владельца {owner_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    templates = await self.repository.get_by_owner(owner_id)
                    log_info(f"Получено {len(templates)} шаблонов для владельца {owner_id}", service="survey-service")
                    return templates
                except Exception as e:
                    log_error(f"Ошибка получения шаблонов владельца {owner_id}: {e}", service="survey-service")
                    raise