import uuid
from reforma_authorization.domain.repositories.user_repository import UserRepository
from reforma_authorization.domain.entities.user import User
from reforma_authorization.domain.entities.email_verification_token import EmailVerificationToken
from datetime import datetime, timedelta
import secrets

from reforma_authorization.domain.repositories.email_verification_token_repository import EmailVerificationTokenRepository
from reforma_authorization.infrastructure.rabbitmq.publisher import EventPublisher
from reforma_authorization.infrastructure.security.password_hasher import BcryptPasswordHasher
from reforma_authorization.common.logger import log_info
from reforma_authorization.infrastructure.config.rabbitmq_config import (
    EMAIL_VERIFICATION_ROUTING_KEY,
    MAIL_EXCHANGE, 
    USER_EXCHANGE, 
    USER_CREATE_ROUTING_KEY
)

class RegisterUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: EmailVerificationTokenRepository,
        password_hasher: BcryptPasswordHasher,
        event_publisher: EventPublisher
    ):
        self.user_repo = user_repo
        self.token_repo = token_repo
        self.password_hasher = password_hasher
        self.event_publisher = event_publisher

    async def execute(self, username: str, email: str, password: str):
        if await self.user_repo.get_by_email(email):
            raise ValueError("User with this email already exists")

        if await self.user_repo.get_by_username(username):
            raise ValueError("User with this username already exists")

        hashed_password = self.password_hasher.hash(password)

        user = await self.user_repo.create(
            User(id=uuid.uuid4(), username=username, email=email, password_hash=hashed_password)
        )

        token = await self.token_repo.create_token(user.id, hours_valid=24)
        log_info(f"token created, token={token}", service="auth-service")

        await self.event_publisher.publish_event(
            exchange_name=USER_EXCHANGE,
            event_type=USER_CREATE_ROUTING_KEY,
            payload={
                "user_id": str(user.id),
                "username": user.username,
                "email": user.email
            }
        )

        await self.event_publisher.publish_event(
            exchange_name=MAIL_EXCHANGE,
            event_type=EMAIL_VERIFICATION_ROUTING_KEY,
            payload={
                "user_id": str(user.id),
                "email": user.email,
                "token": token.token,
                "username": user.username
            }
        )

        log_info("Publisher send event", service="auth-service")

        return user
    