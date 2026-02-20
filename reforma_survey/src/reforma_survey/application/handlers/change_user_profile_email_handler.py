from reforma_survey.infrastructure.repositories.user_profile_repository_impl import (
    UserProfileRepositoryImpl,
)
from reforma_survey.infrastructure.db.session import SessionLocal


class ChangeUserProfileEmailHandler:
    async def handle(self, payload: dict):
        user_id = payload.get("user_id")
        new_email = payload.get("new_email")
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    repo = UserProfileRepositoryImpl(db)
                    await repo.update_email(user_id, new_email)
                except Exception:
                    raise
