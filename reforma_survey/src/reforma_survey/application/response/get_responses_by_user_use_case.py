from typing import List
from uuid import UUID

from reforma_survey.domain.entities.response import Response
from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class GetResponsesByUserUseCase:
    def __init__(self, repository: ResponseRepository):
        self.repository = repository

    async def execute(self, user_id: UUID) -> List[Response]:
        log_info(f"Начало получения всех ответов пользователя {user_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    responses = await self.repository.get_by_user(user_id)
                    log_info(f"Получено {len(responses)} ответов пользователя {user_id}", service="survey-service")
                    return responses
                except Exception as e:
                    log_error(f"Ошибка получения ответов пользователя {user_id}: {e}", service="survey-service")
                    raise