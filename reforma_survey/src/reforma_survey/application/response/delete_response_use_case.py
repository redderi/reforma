from uuid import UUID

from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info


class DeleteResponseUseCase:
    def __init__(self, repository: ResponseRepository):
        self.repository = repository

    async def execute(self, response_id: UUID) -> None:
        log_info(f"Удаление ответа {response_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                await self.repository.delete(response_id)
                log_info(f"Ответ {response_id} удалён", service="survey-service")