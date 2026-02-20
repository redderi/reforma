from uuid import UUID, uuid4
from typing import Dict, Any
from reforma_survey.domain.entities.survey import Survey
from reforma_survey.domain.repositories.survey_repository import SurveyRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class CreateSurveyUseCase:
    def __init__(self, repository: SurveyRepository):
        self.repository = repository

    async def execute(self, data: Dict[str, Any], owner_id: UUID) -> Survey:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    survey = Survey(
                        id=uuid4(),
                        owner_id=owner_id,
                        title=data.get("title", "").strip(),
                        description=data.get("description"),
                        settings=data.get("settings", {}),
                        template_id=data.get("template_id"),
                        published=False,
                        questions=[],
                    )
                    if not survey.title:
                        raise ValueError("Survey title is required")
                    created = await self.repository.create(survey)
                    return created

                except ValueError:
                    raise
                except Exception:
                    raise
