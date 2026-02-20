from uuid import UUID
from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class DeleteResponseUseCase:
    def __init__(self, repository: ResponseRepository):
        self.repository = repository

    async def execute(self, response_id: UUID) -> None:
        async with SessionLocal() as db:
            async with db.begin():
                await self.repository.delete(response_id)
