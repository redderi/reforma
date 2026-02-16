from reforma_authorization.domain.repositories.user_repository import UserRepository
from reforma_authorization.infrastructure.repositories.email_verification_token_impl import EmailTokenRepositoryImpl
from reforma_authorization.infrastructure.rabbitmq.publisher import EventPublisher
from reforma_authorization.infrastructure.config.rabbitmq_config import MAIL_EXCHANGE, USER_RESTORE_ROUTING_KEY
from reforma_common.logger import log_info
from uuid import UUID
from reforma_authorization.domain.entities.user import UserStatus

class RestoreUserByAdminUseCase:
    def __init__(
        self, 
        user_repo: UserRepository, 
    ):
        self.user_repo = user_repo

    async def execute(self, user_id: UUID):
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        if user.status != UserStatus.DEACTIVATED:
            raise ValueError("User cannot be restored")

        user.status = UserStatus.ACTIVE
        user.deleted_at = None
        await self.user_repo.update(user)

        log_info(f"User restored successfully: user_id={user.id}", service="auth-service")
        return {"message": "Аккаунт успешно восстановлен и активирован"}
