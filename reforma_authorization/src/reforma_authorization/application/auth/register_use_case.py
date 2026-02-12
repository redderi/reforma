from reforma_authorization.domain.repositories.user_repository import UserRepository
from reforma_authorization.domain.entities.user import User
from reforma_authorization.domain.entities.email_verification_token import EmailVerificationToken
from datetime import datetime, timedelta
import secrets

from reforma_authorization.domain.repositories.email_verification_token import EmailVerificationTokenRepository
from reforma_authorization.infrastructure.rabbitmq.publisher import MailPublisher
from reforma_authorization.infrastructure.security.password_hasher import BcryptPasswordHasher
from reforma_authorization.common.logger import log_info
from reforma_authorization.infrastructure.config.rabbitmq_config import EMAIL_VERIFICATION_ROUTING_KEY

class RegisterUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: EmailVerificationTokenRepository,
        password_hasher: BcryptPasswordHasher,
        mail_publisher: MailPublisher
    ):
        self.user_repo = user_repo
        self.token_repo = token_repo
        self.password_hasher = password_hasher
        self.mail_publisher = mail_publisher

    async def execute(self, username: str, email: str, password: str):
        if self.user_repo.get_by_email(email):
            raise ValueError("User with this email already exists")
        if self.user_repo.get_by_username(username):
            raise ValueError("User with this username already exists")

        hashed_password = self.password_hasher.hash(password)
        user = self.user_repo.create(
            User(id=0, username=username, email=email, password_hash=hashed_password)
        )

        token = self.token_repo.create_token(user.id, hours_valid=24)
        log_info(f"token created, token={token}", service="auth-service")

        await self.mail_publisher.send_event(
            EMAIL_VERIFICATION_ROUTING_KEY,
            {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "token": token.token
            }
        )
        log_info("Publisher send event", service="auth-service")

        return user
