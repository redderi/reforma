from uuid import UUID
from typing import Dict, Any

from reforma_survey.domain.entities.template import Template
from reforma_survey.domain.repositories.template_repository import TemplateRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class CreateTemplateUseCase:
    def __init__(self, repository: TemplateRepository):
        self.repository = repository

    async def execute(self, data: Dict[str, Any], owner_id: UUID) -> Template:
        log_info(f"Начало создания шаблона для владельца {owner_id}, name={data.get('name')}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    template = Template(
                        id=UUID(),
                        owner_id=owner_id,
                        name=data.get("name", "").strip(),
                        description=data.get("description"),
                        survey_style=data.get("survey_style", {}),
                        question_style=data.get("question_style", {}),
                        assets=data.get("assets", []),
                    )

                    if not template.name:
                        raise ValueError("Название шаблона обязательно")

                    created = await self.repository.create(template)

                    log_info(f"Шаблон успешно создан: id={created.id}, name={created.name}", service="survey-service")
                    return created

                except ValueError as ve:
                    log_error(f"Ошибка валидации при создании шаблона: {ve}", service="survey-service")
                    raise
                except Exception as e:
                    log_error(f"Неожиданная ошибка при создании шаблона: {e}", service="survey-service")
                    raise