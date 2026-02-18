from uuid import UUID

from reforma_survey.domain.repositories.question_repository import QuestionRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info


class QuestionExistsUseCase:
    def __init__(self, repository: QuestionRepository):
        self.repository = repository

    async def execute(self, question_id: UUID) -> bool:
        log_info(f"Проверка существования вопроса {question_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                exists = await self.repository.exists(question_id)
                log_info(f"Вопрос {question_id} существует: {exists}", service="survey-service")
                return exists