from uuid import UUID
from reforma_survey.domain.repositories.question_repository import QuestionRepository


class GetNextOrderUseCase:
    def __init__(self, repository: QuestionRepository):
        self.repository = repository

    async def execute(self, survey_id: UUID) -> int:
        try:
            next_order = await self.repository.get_next_order(survey_id)
            return next_order
        except ValueError:
            raise
        except Exception:
            raise
