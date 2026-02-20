from reforma_survey.domain.entities.question import Question
from reforma_survey.domain.repositories.question_repository import QuestionRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class CreateQuestionUseCase:
    def __init__(self, repository: QuestionRepository):
        self.repository = repository

    async def execute(self, question: Question) -> Question:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    created = await self.repository.create(question)
                    return created
                except Exception:
                    raise
