from reforma_survey.infrastructure.repositories.user_profile_repository_impl import UserProfileRepositoryImpl
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_survey.domain.entities.user_profile import UserProfile

class UserCreatedHandler:
    async def handle(self, payload: dict):
        async with SessionLocal() as db:
            async with db.begin():  
                repo = UserProfileRepositoryImpl(db)
                await repo.create(
                    UserProfile(
                        id=payload["user_id"],
                        username=payload["username"],
                        email=payload["email"]
                    )
                )