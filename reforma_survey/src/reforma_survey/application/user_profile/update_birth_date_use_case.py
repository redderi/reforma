from uuid import UUID
from datetime import date
from reforma_survey.domain.entities.user_profile import UserProfile
from reforma_survey.domain.repositories.user_profile_repository import (
    UserProfileRepository,
)
from reforma_survey.infrastructure.db.session import SessionLocal


class UpdateBirthDateUseCase:
    def __init__(self, repository: UserProfileRepository):
        self.repository = repository

    async def execute(self, user_id: UUID, birth_date: date | None) -> UserProfile:
        async with SessionLocal() as db:
            async with db.begin():
                updated = await self.repository.update_birth_date(user_id, birth_date)
            return updated
