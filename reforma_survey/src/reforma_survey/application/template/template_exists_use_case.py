from uuid import UUID

from reforma_survey.domain.repositories.template_repository import TemplateRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info


class TemplateExistsUseCase:
    def __init__(self, repository: TemplateRepository):
        self.repository = repository

    async def execute(self, template_id: UUID) -> bool:
        log_info(f"Проверка существования шаблона {template_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                exists = await self.repository.exists(template_id)
                log_info(f"Шаблон {template_id} существует: {exists}", service="survey-service")
                return exists