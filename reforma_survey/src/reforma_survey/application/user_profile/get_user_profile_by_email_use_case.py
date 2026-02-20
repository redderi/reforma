from reforma_survey.domain.entities.user_profile import UserProfile
from reforma_survey.domain.repositories.user_profile_repository import (
    UserProfileRepository,
)
from reforma_survey.infrastructure.db.session import SessionLocal


class GetUserProfileByEmailUseCase:
    def __init__(self, repository: UserProfileRepository):
        self.repository = repository

    async def execute(self, email: str) -> UserProfile | None:
        async with SessionLocal() as db:
            async with db.begin():
                profile = await self.repository.get_by_email(email)
                return profile
