from uuid import UUID, uuid4
from typing import Dict, Any
from reforma_survey.domain.entities.template import Template
from reforma_survey.domain.repositories.template_repository import TemplateRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class CreateTemplateUseCase:
    def __init__(self, repository: TemplateRepository):
        self.repository = repository

    async def execute(self, data: Dict[str, Any], owner_id: UUID) -> Template:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    template = Template(
                        id=uuid4(),
                        owner_id=owner_id,
                        name=data.get("name", "").strip(),
                        description=data.get("description"),
                        survey_style=data.get("survey_style", {}),
                        question_style=data.get("question_style", {}),
                        assets=data.get("assets", []),
                    )

                    if not template.name:
                        raise ValueError("Template name is required")
                    created = await self.repository.create(template)
                    return created
                except ValueError:
                    raise
                except Exception:
                    raise
