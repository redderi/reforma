from reforma_common.logger import log_error, log_info, log_warning
from reforma_survey.infrastructure.repositories.user_profile_repository_impl import UserProfileRepositoryImpl
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_survey.infrastructure.db.models import UserProfileModel

class UserDeletedHandler:
    async def handle(self, payload: dict):
        user_id = payload.get("user_id")
        if not user_id:
            log_error("No user_id in delete payload", service="survey_service")
            raise ("No user_id in delete payload") 

        async with SessionLocal() as db:
            async with db.begin():  
                repo = UserProfileRepositoryImpl(db)
                model = await db.get(UserProfileModel, user_id)
                if not model:
                    log_warning(f"UserProfile {user_id} not found for deletion", service="survey_service")
                    raise ("UserProfile {user_id} not found for deletion") 

                await repo.delete(user_id)
                log_info(f"UserProfile {user_id} deleted successfully", service="survey_service")