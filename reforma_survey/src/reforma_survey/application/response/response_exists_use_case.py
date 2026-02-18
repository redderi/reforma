from uuid import UUID

from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info


class ResponseExistsUseCase:
    def __init__(self, repository: ResponseRepository):
        self.repository = repository

    async def execute(self, response_id: UUID) -> bool:
        log_info(f"Проверка существования ответа {response_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                exists = await self.repository.exists(response_id)
                log_info(f"Ответ {response_id} существует: {exists}", service="survey-service")
                return exists