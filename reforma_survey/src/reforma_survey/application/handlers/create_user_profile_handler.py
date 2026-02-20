from reforma_survey.infrastructure.repositories.user_profile_repository_impl import (
    UserProfileRepositoryImpl,
)
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_survey.domain.entities.user_profile import UserProfile


class CreateUserProfileHandler:
    async def handle(self, payload: dict):
        user_id = payload.get("user_id")
        username = payload.get("username")
        email = payload.get("email")
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    repo = UserProfileRepositoryImpl(db)
                    await repo.create(
                        UserProfile(id=user_id, username=username, email=email)
                    )
                except Exception:
                    raise
