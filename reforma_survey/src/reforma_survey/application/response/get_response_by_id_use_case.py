from uuid import UUID

from reforma_survey.domain.entities.response import Response
from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_warning, log_error


class GetResponseByIdUseCase:
    def __init__(self, repository: ResponseRepository):
        self.repository = repository

    async def execute(self, response_id: UUID) -> Response | None:
        log_info(f"Начало получения ответа по ID: {response_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    response = await self.repository.get_by_id(response_id)
                    if response:
                        log_info(f"Ответ успешно получен: {response_id}", service="survey-service")
                    else:
                        log_warning(f"Ответ не найден: {response_id}", service="survey-service")
                    return response
                except Exception as e:
                    log_error(f"Ошибка при получении ответа {response_id}: {e}", service="survey-service")
                    raise