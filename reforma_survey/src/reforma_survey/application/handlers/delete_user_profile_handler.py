from reforma_survey.infrastructure.repositories.user_profile_repository_impl import (
    UserProfileRepositoryImpl,
)
from reforma_survey.infrastructure.db.session import SessionLocal


class DeleteUserProfileHandler:
    async def handle(self, payload: dict):
        user_id = payload.get("user_id")
        if not user_id:
            raise ValueError("No user_id in delete payload")

        async with SessionLocal() as db:
            async with db.begin():
                repo = UserProfileRepositoryImpl(db)
                model = await repo.get_by_id(user_id)
                if not model:
                    raise ValueError(f"UserProfile {user_id} not found")

                await repo.delete(user_id)
