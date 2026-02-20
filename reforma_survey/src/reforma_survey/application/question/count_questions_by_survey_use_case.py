from uuid import UUID
from reforma_survey.domain.repositories.question_repository import QuestionRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class CountQuestionsBySurveyUseCase:
    def __init__(self, repository: QuestionRepository):
        self.repository = repository

    async def execute(self, survey_id: UUID) -> int:
        async with SessionLocal() as db:
            async with db.begin():
                count = await self.repository.count_by_survey(survey_id)
                return count
