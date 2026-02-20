from uuid import UUID
from reforma_survey.domain.entities.response import Response
from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class GetResponseByIdUseCase:
    def __init__(self, repository: ResponseRepository):
        self.repository = repository

    async def execute(self, response_id: UUID) -> Response | None:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    response = await self.repository.get_by_id(response_id)
                    return response
                except Exception:
                    raise
