from uuid import UUID

from reforma_survey.domain.entities.template import Template
from reforma_survey.domain.repositories.template_repository import TemplateRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_warning, log_error


class GetTemplateByIdUseCase:
    def __init__(self, repository: TemplateRepository):
        self.repository = repository

    async def execute(self, template_id: UUID) -> Template | None:
        log_info(f"Начало получения шаблона по ID: {template_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    template = await self.repository.get_by_id(template_id)
                    if template:
                        log_info(f"Шаблон успешно получен: {template_id}, name={template.name}", service="survey-service")
                    else:
                        log_warning(f"Шаблон не найден: {template_id}", service="survey-service")
                    return template
                except Exception as e:
                    log_error(f"Ошибка при получении шаблона {template_id}: {e}", service="survey-service")
                    raise