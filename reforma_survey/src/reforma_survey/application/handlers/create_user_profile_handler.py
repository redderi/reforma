from reforma_common.logger import log_error, log_info
from reforma_survey.infrastructure.repositories.user_profile_repository_impl import UserProfileRepositoryImpl
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_survey.domain.entities.user_profile import UserProfile

class CreateUserProfileHandler:
    async def handle(self, payload: dict):
        user_id = payload.get("user_id")
        username = payload.get("username")
        email = payload.get("email")
        log_info(f"Creating user profile: {user_id}, {username}, {email}", service="survey-service")
        async with SessionLocal() as db:
            async with db.begin():  
                try:
                    repo = UserProfileRepositoryImpl(db)
                    user = await repo.create(
                        UserProfile(
                            id=user_id,
                            username=username,
                            email=email
                        )
                    )
                    log_info(f"User profile created successfully: {user.id}", service="survey-service")
                except Exception as e:
                    log_error(f"Failed to create user profile {user_id}: {e}", service="survey-service")
                    raise