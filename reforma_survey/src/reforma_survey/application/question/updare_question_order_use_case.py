from uuid import UUID
from reforma_survey.domain.entities.question import Question
from reforma_survey.domain.repositories.question_repository import QuestionRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class UpdateQuestionOrderUseCase:
    def __init__(self, repository: QuestionRepository):
        self.repository = repository

    async def execute(self, question_id: UUID, new_order: int) -> Question:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.update_order(question_id, new_order)
                    return updated
                except Exception:
                    raise
