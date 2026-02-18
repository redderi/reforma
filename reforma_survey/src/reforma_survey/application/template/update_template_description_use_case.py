from uuid import UUID

from reforma_survey.domain.entities.template import Template
from reforma_survey.domain.repositories.template_repository import TemplateRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class UpdateTemplateDescriptionUseCase:
    def __init__(self, repository: TemplateRepository):
        self.repository = repository

    async def execute(self, template_id: UUID, description: str | None) -> Template:
        log_info(f"Обновление описания шаблона {template_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.update_description(template_id, description)
                    log_info(f"Описание шаблона {template_id} обновлено", service="survey-service")
                    return updated
                except Exception as e:
                    log_error(f"Ошибка обновления описания шаблона {template_id}: {e}", service="survey-service")
                    raise