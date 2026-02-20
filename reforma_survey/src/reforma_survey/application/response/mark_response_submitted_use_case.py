from datetime import datetime
from uuid import UUID
from reforma_survey.domain.entities.response import Response
from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class MarkResponseSubmittedUseCase:
    def __init__(self, repository: ResponseRepository):
        self.repository = repository

    async def execute(
        self, response_id: UUID, submitted_at: datetime = None
    ) -> Response:
        async with SessionLocal() as db:
            async with db.begin():
                updated = await self.repository.mark_submitted(
                    response_id, submitted_at
                )
                return updated
