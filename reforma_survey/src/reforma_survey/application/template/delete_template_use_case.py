from uuid import UUID

from reforma_survey.domain.repositories.template_repository import TemplateRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class DeleteTemplateUseCase:
    def __init__(self, repository: TemplateRepository):
        self.repository = repository

    async def execute(self, template_id: UUID) -> None:
        log_info(f"Начало удаления шаблона {template_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    await self.repository.delete(template_id)
                    log_info(f"Шаблон {template_id} успешно удалён", service="survey-service")
                except Exception as e:
                    log_error(f"Ошибка удаления шаблона {template_id}: {e}", service="survey-service")
                    raise