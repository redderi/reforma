from reforma_common.logger import log_error, log_info
from reforma_survey.infrastructure.repositories.user_profile_repository_impl import UserProfileRepositoryImpl
from reforma_survey.infrastructure.db.session import SessionLocal

class ChangeUserProfileUsernameHandler:
    async def handle(self, payload: dict):
        user_id = payload.get("user_id")
        new_username = payload.get("new_username")
        log_info(f"Changing username for user {user_id} to {new_username}", service="survey-service")
        async with SessionLocal() as db:
            async with db.begin():  
                try:
                    repo = UserProfileRepositoryImpl(db)
                    user = await repo.update_username(user_id, new_username)
                    log_info(f"Username updated successfully for user {user.id}: {user.username}", service="survey-service")
                except Exception as e:
                    log_error(f"Failed to update username for user {user_id}: {e}", service="survey-service")
                    raise