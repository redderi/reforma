from uuid import UUID
from reforma_survey.domain.repositories.question_repository import QuestionRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class QuestionExistsUseCase:
    def __init__(self, repository: QuestionRepository):
        self.repository = repository

    async def execute(self, question_id: UUID) -> bool:
        async with SessionLocal() as db:
            async with db.begin():
                exists = await self.repository.exists(question_id)
                return exists
