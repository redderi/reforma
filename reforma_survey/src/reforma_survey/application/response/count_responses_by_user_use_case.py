from uuid import UUID

from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info


class CountResponsesByUserUseCase:
    def __init__(self, repository: ResponseRepository):
        self.repository = repository

    async def execute(self, user_id: UUID) -> int:
        log_info(f"Подсчёт ответов пользователя {user_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                count = await self.repository.count_by_user(user_id)
                log_info(f"Пользователь {user_id} дал {count} ответов", service="survey-service")
                return count