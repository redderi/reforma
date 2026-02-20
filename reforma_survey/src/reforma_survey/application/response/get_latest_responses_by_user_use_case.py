from typing import List
from uuid import UUID
from reforma_survey.domain.entities.response import Response
from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class GetLatestResponsesByUserUseCase:
    def __init__(self, repository: ResponseRepository):
        self.repository = repository

    async def execute(self, user_id: UUID, limit: int = 10) -> List[Response]:
        async with SessionLocal() as db:
            async with db.begin():
                responses = await self.repository.get_latest_by_user(
                    user_id=user_id, limit=limit
                )
                return responses
