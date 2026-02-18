from reforma_common.logger import log_error, log_info
from reforma_survey.infrastructure.repositories.user_profile_repository_impl import UserProfileRepositoryImpl
from reforma_survey.infrastructure.db.session import SessionLocal

class AddBalanceHandler:
    async def handle(self, payload: dict):
        user_id = payload.get("user_id")
        amount = payload.get("amount")
        log_info(f"Adding balance {amount} to user {user_id}", service="survey-service")
        async with SessionLocal() as db:
            async with db.begin():  
                try:
                    repo = UserProfileRepositoryImpl(db)
                    user = await repo.add_balance(user_id=user_id, amount=amount)
                    log_info(f"Balance updated successfully for user {user.id}, new balance: {user.balance}", service="survey-service")
                except Exception as e:
                    log_error(f"Failed to add balance for user {user_id}: {e}", service="survey-service")
                    raise