from uuid import UUID

from reforma_survey.domain.entities.template import Template
from reforma_survey.domain.repositories.template_repository import TemplateRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class AddTemplateAssetUseCase:
    def __init__(self, repository: TemplateRepository):
        self.repository = repository

    async def execute(self, template_id: UUID, asset_url: str) -> Template:
        log_info(f"Добавление ассета {asset_url} в шаблон {template_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.add_asset(template_id, asset_url)
                    log_info(f"Ассет {asset_url} добавлен в шаблон {template_id}", service="survey-service")
                    return updated
                except Exception as e:
                    log_error(f"Ошибка добавления ассета в шаблон {template_id}: {e}", service="survey-service")
                    raise