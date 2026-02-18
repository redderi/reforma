from reforma_survey.infrastructure.repositories.user_profile_repository_impl import UserProfileRepositoryImpl
from reforma_survey.infrastructure.db.session import SessionLocal

class ChangeUserProfileEmailHandler:
    async def handle(self, payload: dict):
        async with SessionLocal() as db:
            async with db.begin():  
                repo = UserProfileRepositoryImpl(db)
                await repo.update_email(payload["user_id"], payload["new_email"])