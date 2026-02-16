from reforma_authorization.domain.repositories.user_repository import UserRepository
from uuid import UUID
from reforma_authorization.infrastructure.rabbitmq.publisher import EventPublisher
from reforma_authorization.infrastructure.config.rabbitmq_config import USER_DELETE_ROUTING_KEY, USER_EXCHANGE
from reforma_common.logger import log_info

class HardDeleteUserByIdUseCase:

    def __init__(self, user_repo: UserRepository, event_publisher: EventPublisher):
        self.user_repo = user_repo
        self.event_publisher = event_publisher

    async def execute(self, user_id: UUID):
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        await self.user_repo.hard_delete_by_id(user_id)

        await self.event_publisher.publish_event(
            exchange_name=USER_EXCHANGE,
            event_type=USER_DELETE_ROUTING_KEY,
            payload={
                "user_id": str(user.id),
                "username": user.username,
                "email": user.email
            }
        )
        log_info(f"Publisher sent delete event for user_id={user.id}", service="auth-service")

        return user
