from uuid import UUID
from reforma_survey.domain.entities.question import Question
from reforma_survey.domain.repositories.question_repository import QuestionRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class UpdateQuestionTypeUseCase:
    def __init__(self, repository: QuestionRepository):
        self.repository = repository

    async def execute(self, question_id: UUID, new_type: str) -> Question:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.update_type(question_id, new_type)
                    return updated
                except Exception:
                    raise
