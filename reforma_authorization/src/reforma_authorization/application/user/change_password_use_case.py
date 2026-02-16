from reforma_authorization.domain.repositories.user_repository import UserRepository
from reforma_authorization.domain.services.password_hasher import PasswordHasher
from reforma_authorization.domain.repositories.refresh_token_repository import RefreshTokenRepository
from reforma_common.logger import log_info
from reforma_authorization.infrastructure.config.rabbitmq_config import (
    CHANGE_PASSWORD_ROUTING_KEY,
    MAIL_EXCHANGE, 
)
from reforma_authorization.infrastructure.rabbitmq.publisher import EventPublisher
from reforma_authorization.domain.repositories.email_verification_token_repository import EmailVerificationTokenRepository

class ChangePasswordUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        refresh_token_repo: RefreshTokenRepository,
        password_hasher: PasswordHasher,
        token_repo: EmailVerificationTokenRepository,
        event_publisher: EventPublisher
    ):
        self.user_repo = user_repo
        self.refresh_token_repo = refresh_token_repo
        self.password_hasher = password_hasher
        self.token_repo = token_repo
        self.event_publisher = event_publisher

    async def execute(self, user_id: str, old_password: str, new_password: str):
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        if not self.password_hasher.verify(old_password, user.password_hash):
            raise ValueError("Wrong old password")

        new_hash = self.password_hasher.hash(new_password)

        token = await self.token_repo.create_token(
            user.id,
            hours_valid=24,
            data={"new_password_hash": new_hash}
        )
        log_info(f"Token created: {token.token}", service="auth-service")

        await self.event_publisher.publish_event(
            exchange_name=MAIL_EXCHANGE,
            event_type=CHANGE_PASSWORD_ROUTING_KEY,
            payload={
                "user_id": str(user.id),
                "email": user.email,
                "token": token.token,
                "username": user.username
            }
        )

        log_info("Password change email sent", service="auth-service")
