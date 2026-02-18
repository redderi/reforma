from uuid import UUID
from datetime import datetime

from reforma_survey.domain.entities.response import Response
from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class MarkResponseSubmittedUseCase:
    def __init__(self, repository: ResponseRepository):
        self.repository = repository

    async def execute(self, response_id: UUID, submitted_at: datetime) -> Response:
        log_info(f"Отметка ответа {response_id} как отправленного ({submitted_at})", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.mark_submitted(response_id, submitted_at)
                    log_info(f"Ответ {response_id} отмечен как отправленный", service="survey-service")
                    return updated
                except Exception as e:
                    log_error(f"Ошибка отметки ответа {response_id} как отправленного: {e}", service="survey-service")
                    raise