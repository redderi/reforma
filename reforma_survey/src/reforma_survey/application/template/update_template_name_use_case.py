from uuid import UUID

from reforma_survey.domain.entities.template import Template
from reforma_survey.domain.repositories.template_repository import TemplateRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class UpdateTemplateNameUseCase:
    def __init__(self, repository: TemplateRepository):
        self.repository = repository

    async def execute(self, template_id: UUID, new_name: str) -> Template:
        log_info(f"Обновление имени шаблона {template_id} → {new_name}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.update_name(template_id, new_name)
                    log_info(f"Имя шаблона {template_id} обновлено на {new_name}", service="survey-service")
                    return updated
                except ValueError as ve:
                    log_error(f"Ошибка валидации имени шаблона {template_id}: {ve}", service="survey-service")
                    raise
                except Exception as e:
                    log_error(f"Ошибка обновления имени шаблона {template_id}: {e}", service="survey-service")
                    raise