from uuid import UUID
from typing import Dict

from reforma_survey.domain.entities.template import Template
from reforma_survey.domain.repositories.template_repository import TemplateRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class UpdateTemplateQuestionStyleUseCase:
    def __init__(self, repository: TemplateRepository):
        self.repository = repository

    async def execute(self, template_id: UUID, question_style: Dict) -> Template:
        log_info(f"Обновление базовых стилей вопросов шаблона {template_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.update_question_style(template_id, question_style)
                    log_info(f"Базовые стили вопросов шаблона {template_id} обновлены", service="survey-service")
                    return updated
                except Exception as e:
                    log_error(f"Ошибка обновления стилей вопросов шаблона {template_id}: {e}", service="survey-service")
                    raise