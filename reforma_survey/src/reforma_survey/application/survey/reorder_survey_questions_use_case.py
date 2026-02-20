from uuid import UUID
from typing import List
from reforma_survey.domain.entities.survey import Survey
from reforma_survey.domain.repositories.survey_repository import SurveyRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class ReorderSurveyQuestionsUseCase:
    def __init__(self, repository: SurveyRepository):
        self.repository = repository

    async def execute(self, survey_id: UUID, question_ids: List[UUID]) -> Survey:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.reorder_questions(
                        survey_id, question_ids
                    )
                    return updated
                except ValueError:
                    raise
                except Exception:
                    raise
