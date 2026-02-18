from uuid import UUID

from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class DeleteResponseUseCase:
    def __init__(self, repository: ResponseRepository):
        self.repository = repository

    async def execute(self, response_id: UUID) -> None:
        log_info(f"Начало удаления ответа {response_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    await self.repository.delete(response_id)
                    log_info(f"Ответ {response_id} успешно удалён", service="survey-service")
                except Exception as e:
                    log_error(f"Ошибка удаления ответа {response_id}: {e}", service="survey-service")
                    raise