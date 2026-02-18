from uuid import UUID
from typing import Dict, Any

from reforma_survey.domain.entities.response import Response
from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class UpdateResponseAnswersUseCase:
    def __init__(self, repository: ResponseRepository):
        self.repository = repository

    async def execute(self, response_id: UUID, new_answers: Dict[UUID, Any]) -> Response:
        log_info(f"Обновление ответов в записи {response_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.update_answers(response_id, new_answers)
                    log_info(f"Ответы в записи {response_id} успешно обновлены", service="survey-service")
                    return updated
                except Exception as e:
                    log_error(f"Ошибка обновления ответов в записи {response_id}: {e}", service="survey-service")
                    raise