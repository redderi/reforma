from reforma_authorization.domain.repositories.user_repository import UserRepository
from reforma_authorization.infrastructure.rabbitmq.publisher import EventPublisher
from reforma_authorization.infrastructure.config.rabbitmq_config import (
    MAIL_EXCHANGE,
    USER_RESTORE_ROUTING_KEY,
)
from reforma_authorization.domain.repositories.email_verification_token_repository import (
    EmailVerificationTokenRepository,
)
from uuid import UUID
from reforma_authorization.domain.entities.user import UserStatus


class RestoreUserUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: EmailVerificationTokenRepository,
        event_publisher: EventPublisher,
    ):
        self.user_repo = user_repo
        self.token_repo = token_repo
        self.event_publisher = event_publisher

    async def execute(self, user_id: UUID):
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        if user.status != UserStatus.DEACTIVATED:
            raise ValueError("User cannot be restored")
        token = await self.token_repo.create_token(user.id, hours_valid=24)
        await self.event_publisher.publish_event(
            exchange_name=MAIL_EXCHANGE,
            event_type=USER_RESTORE_ROUTING_KEY,
            payload={
                "user_id": str(user.id),
                "username": user.username,
                "email": user.email,
                "token": token,
            },
        )