from reforma_authorization.domain.repositories.user_repository import UserRepository
from reforma_authorization.domain.repositories.refresh_token_repository import RefreshTokenRepository
from reforma_authorization.infrastructure.rabbitmq.publisher import EventPublisher
from reforma_authorization.infrastructure.config.rabbitmq_config import (
    USER_EXCHANGE,
    USER_DELETE_ROUTING_KEY
)
from reforma_authorization.domain.entities.user import User


class SoftDeleteUserUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        refresh_token_repo: RefreshTokenRepository,
        event_publisher: EventPublisher
    ):
        self.user_repo = user_repo
        self.refresh_token_repo = refresh_token_repo
        self.event_publisher = event_publisher

    async def execute(self, user_id: str) -> None:
        user: User | None = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        await self.refresh_token_repo.delete_all_by_user(user_id)

        await self.user_repo.delete(user)

        await self.event_publisher.publish_event(
            exchange_name=USER_EXCHANGE,
            event_type=USER_DELETE_ROUTING_KEY,
            payload={"user_id": str(user.id)}
        )
