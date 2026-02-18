from reforma_common.logger import log_error, log_info
from reforma_survey.infrastructure.repositories.user_profile_repository_impl import UserProfileRepositoryImpl
from reforma_survey.infrastructure.db.session import SessionLocal

class ChangeUserProfileEmailHandler:
    async def handle(self, payload: dict):
        user_id = payload.get("user_id")
        new_email = payload.get("new_email")
        log_info(f"Changing email for user {user_id} to {new_email}", service="survey-service")
        async with SessionLocal() as db:
            async with db.begin():  
                try:
                    repo = UserProfileRepositoryImpl(db)
                    user = await repo.update_email(user_id, new_email)
                    log_info(f"Email updated successfully for user {user.id}: {user.email}", service="survey-service")
                except Exception as e:
                    log_error(f"Failed to update email for user {user_id}: {e}", service="survey-service")
                    raise