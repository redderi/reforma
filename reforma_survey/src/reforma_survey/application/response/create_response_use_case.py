from uuid import UUID

from reforma_survey.domain.entities.response import Response
from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info


class CreateResponseUseCase:
    def __init__(self, repository: ResponseRepository):
        self.repository = repository

    async def execute(self, response: Response) -> Response:
        log_info(f"Создание ответа на опрос {response.survey_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                created = await self.repository.create(response)
                log_info(f"Ответ успешно создан: id={created.id}", service="survey-service")
                return created