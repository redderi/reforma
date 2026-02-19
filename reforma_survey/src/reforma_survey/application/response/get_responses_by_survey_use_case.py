from typing import List
from uuid import UUID

from reforma_survey.domain.entities.response import Response
from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info


class GetResponsesBySurveyUseCase:
    def __init__(self, repository: ResponseRepository):
        self.repository = repository

    async def execute(
        self,
        survey_id: UUID,
        limit: int = 100,
        offset: int = 0,
        include_anonymous: bool = True
    ) -> List[Response]:
        log_info(f"Получение ответов опроса {survey_id} (limit={limit}, offset={offset})", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                responses = await self.repository.get_by_survey(
                    survey_id=survey_id,
                    limit=limit,
                    offset=offset,
                    include_anonymous=include_anonymous
                )
                log_info(f"Найдено {len(responses)} ответов для опроса {survey_id}", service="survey-service")
                return responses