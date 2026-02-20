from uuid import UUID
from reforma_survey.domain.entities.user_profile import UserProfile
from reforma_survey.domain.repositories.user_profile_repository import (
    UserProfileRepository,
)
from reforma_survey.infrastructure.db.session import SessionLocal


class UpdateProfilePictureUseCase:
    def __init__(self, repository: UserProfileRepository):
        self.repository = repository

    async def execute(self, user_id: UUID, picture_url: str | None) -> UserProfile:
        async with SessionLocal() as db:
            async with db.begin():
                updated = await self.repository.update_profile_picture(
                    user_id, picture_url
                )
            return updated
