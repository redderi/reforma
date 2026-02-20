from uuid import UUID
from reforma_survey.domain.entities.response import Response
from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class CreateResponseUseCase:
    def __init__(self, repository: ResponseRepository):
        self.repository = repository

    async def execute(self, response: Response) -> Response:
        async with SessionLocal() as db:
            async with db.begin():
                created = await self.repository.create(response)
                return created
