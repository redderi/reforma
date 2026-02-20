from uuid import UUID
from typing import Dict
from reforma_survey.domain.entities.question import Question
from reforma_survey.domain.repositories.question_repository import QuestionRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class UpdateQuestionStyleUseCase:
    def __init__(self, repository: QuestionRepository):
        self.repository = repository

    async def execute(self, question_id: UUID, style: Dict) -> Question:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.update_style(question_id, style)
                    return updated
                except Exception:
                    raise
