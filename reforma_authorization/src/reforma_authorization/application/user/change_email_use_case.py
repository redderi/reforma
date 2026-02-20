from reforma_authorization.domain.repositories.user_repository import UserRepository
from reforma_authorization.infrastructure.rabbitmq.publisher import EventPublisher
from reforma_authorization.infrastructure.config.rabbitmq_config import (
    USER_EXCHANGE,
    USER_CHANGE_EMAIL_ROUTING_KEY,
)


class ChangeEmailUseCase:
    def __init__(self, user_repo: UserRepository, event_publisher: EventPublisher):
        self.user_repo = user_repo
        self.event_publisher = event_publisher

    async def execute(self, user_id: int, new_email: str):
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        if await self.user_repo.get_by_email(new_email):
            raise ValueError("Email already exists")
        updated_user = await self.user_repo.change_email(user, new_email)
        await self.event_publisher.publish_event(
            exchange_name=USER_EXCHANGE,
            event_type=USER_CHANGE_EMAIL_ROUTING_KEY,
            payload={"user_id": str(updated_user.id), "new_email": updated_user.email},
        )
        return updated_user
