from uuid import UUID
from reforma_survey.domain.repositories.question_repository import QuestionRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class MoveQuestionUseCase:
    def __init__(self, repository: QuestionRepository):
        self.repository = repository

    async def execute(self, question_id: UUID, survey_id: UUID, new_order: int) -> None:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    await self.repository.move(question_id, survey_id, new_order)
                except Exception:
                    raise
