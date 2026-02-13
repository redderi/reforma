from reforma_authorization.domain.repositories.user_repository import UserRepository
from reforma_authorization.infrastructure.rabbitmq.publisher import EventPublisher
from reforma_authorization.infrastructure.config.rabbitmq_config import (
    USER_EXCHANGE,
    USER_CHANGE_USERNAME_ROUTING_KEY
)

class ChangeUsernameUseCase:

    def __init__(self, user_repo: UserRepository, event_publisher: EventPublisher):
        self.user_repo = user_repo
        self.event_publisher = event_publisher

    async def execute(self, user_id: int, new_username: str):
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        if await self.user_repo.get_by_username(new_username):
            raise ValueError("Username already exists")

        updated_user = await self.user_repo.change_username(user, new_username)

        await self.event_publisher.publish_event(
            exchange_name=USER_EXCHANGE,
            event_type=USER_CHANGE_USERNAME_ROUTING_KEY,
            payload={
                "user_id": str(updated_user.id),
                "new_username": updated_user.username
            }
        )

        return updated_user