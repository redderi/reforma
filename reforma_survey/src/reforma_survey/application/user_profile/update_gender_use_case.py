from uuid import UUID
from reforma_survey.domain.entities.user_profile import UserProfile
from reforma_survey.domain.repositories.user_profile_repository import UserProfileRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class UpdateGenderUseCase:
    def __init__(self, repository: UserProfileRepository):
        self.repository = repository

    async def execute(self, user_id: UUID, gender: str | None) -> UserProfile:
        valid = {None, "male", "female", "other", "prefer_not_to_say"}
        if gender not in valid:
            raise ValueError(f"Invalid gender. Allowed: {valid}")

        async with SessionLocal() as db:
            async with db.begin():
                updated = await self.repository.update_gender(user_id, gender)
                return updated