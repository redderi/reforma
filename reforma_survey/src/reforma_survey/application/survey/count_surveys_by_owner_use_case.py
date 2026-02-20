from uuid import UUID
from reforma_survey.domain.repositories.survey_repository import SurveyRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class CountSurveysByOwnerUseCase:
    def __init__(self, repository: SurveyRepository):
        self.repository = repository

    async def execute(self, owner_id: UUID) -> int:
        async with SessionLocal() as db:
            async with db.begin():
                count = await self.repository.count_by_owner(owner_id)
                return count
