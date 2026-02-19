from typing import Optional
from uuid import UUID

from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info


class HasAlreadyRespondedUseCase:
    def __init__(self, repository: ResponseRepository):
        self.repository = repository

    async def execute(
        self,
        survey_id: UUID,
        user_id: Optional[UUID] = None,
        anonymous_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        fingerprint: Optional[str] = None
    ) -> bool:
        log_info(f"Проверка повторного прохождения опроса {survey_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                has = await self.repository.has_already_responded(
                    survey_id=survey_id,
                    user_id=user_id,
                    anonymous_id=anonymous_id,
                    ip_address=ip_address,
                    fingerprint=fingerprint
                )
                log_info(f"Результат проверки: {'уже отвечал' if has else 'не отвечал'}", service="survey-service")
                return has