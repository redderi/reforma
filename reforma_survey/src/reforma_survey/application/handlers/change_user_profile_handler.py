from reforma_survey.infrastructure.repositories.user_profile_repository_impl import (
    UserProfileRepositoryImpl,
)
from reforma_survey.infrastructure.db.session import SessionLocal


class ChangeUserProfileUsernameHandler:
    async def handle(self, payload: dict):
        user_id = payload.get("user_id")
        new_username = payload.get("new_username")
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    repo = UserProfileRepositoryImpl(db)
                    await repo.update_username(user_id, new_username)
                except Exception:
                    raise
