from typing import List
from reforma_survey.domain.entities.user_profile import UserProfile
from reforma_survey.domain.repositories.user_profile_repository import UserProfileRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class GetAllUserProfilesUseCase:
    def __init__(self, repository: UserProfileRepository):
        self.repository = repository

    async def execute(self) -> List[UserProfile]:
        async with SessionLocal() as db:
            async with db.begin():
                profiles = await self.repository.get_all()
                return profiles