from uuid import UUID
from reforma_survey.domain.entities.question import Question
from reforma_survey.domain.repositories.question_repository import QuestionRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class GetQuestionByIdUseCase:
    def __init__(self, repository: QuestionRepository):
        self.repository = repository

    async def execute(self, question_id: UUID) -> Question | None:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    question = await self.repository.get_by_id(question_id)
                    return question
                except Exception:
                    raise
