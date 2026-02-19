from datetime import datetime
from uuid import UUID

from reforma_survey.domain.entities.response import Response
from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info


class MarkResponseSubmittedUseCase:
    def __init__(self, repository: ResponseRepository):
        self.repository = repository

    async def execute(
        self,
        response_id: UUID,
        submitted_at: datetime = None
    ) -> Response:
        log_info(f"Отправка ответа {response_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                updated = await self.repository.mark_submitted(response_id, submitted_at)
                log_info(f"Ответ {response_id} помечен как отправленный", service="survey-service")
                return updated