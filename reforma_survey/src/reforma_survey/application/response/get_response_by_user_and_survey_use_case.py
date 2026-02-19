from typing import Optional
from uuid import UUID

from reforma_survey.domain.entities.response import Response
from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info


class GetResponseByUserAndSurveyUseCase:
    def __init__(self, repository: ResponseRepository):
        self.repository = repository

    async def execute(
        self,
        survey_id: UUID,
        user_id: Optional[UUID] = None,
        anonymous_id: Optional[str] = None
    ) -> Optional[Response]:
        log_info(f"Поиск ответа пользователя/анонима на опрос {survey_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                response = await self.repository.get_by_user_and_survey(
                    survey_id=survey_id,
                    user_id=user_id,
                    anonymous_id=anonymous_id
                )
                if response:
                    log_info(f"Ответ найден: id={response.id}", service="survey-service")
                else:
                    log_info("Ответ не найден", service="survey-service")
                return response