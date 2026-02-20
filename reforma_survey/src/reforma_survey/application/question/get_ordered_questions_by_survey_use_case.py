from typing import List
from uuid import UUID

from reforma_survey.domain.entities.question import Question
from reforma_survey.domain.repositories.question_repository import QuestionRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class GetOrderedQuestionsBySurveyUseCase:
    def __init__(self, repository: QuestionRepository):
        self.repository = repository

    async def execute(self, survey_id: UUID) -> List[Question]:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    questions = await self.repository.get_by_survey_ordered(survey_id)
                    return questions
                except Exception:
                    raise
