from uuid import UUID
from reforma_survey.domain.entities.response import Response
from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class GetResponseByUserAndSurveyUseCase:
    def __init__(self, repository: ResponseRepository):
        self.repository = repository

    async def execute(
        self,
        survey_id: UUID,
        user_id: UUID | None = None,
        anonymous_id: str | None = None,
    ) -> Response | None:
        async with SessionLocal() as db:
            async with db.begin():
                response = await self.repository.get_by_user_and_survey(
                    survey_id=survey_id, user_id=user_id, anonymous_id=anonymous_id
                )
                return response
