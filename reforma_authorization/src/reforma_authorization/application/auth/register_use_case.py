from reforma_authorization.domain.repositories.user_repository import UserRepository
from reforma_authorization.infrastructure.security.password_hasher import BcryptPasswordHasher
from reforma_authorization.application.email.send_email_verification_event_use_case import SendEmailVerificationEventUseCase
from reforma_authorization.domain.entities.user import User
from reforma_authorization.domain.entities.email_verification_token import EmailVerificationToken
from datetime import datetime, timedelta
import secrets

from reforma_authorization.domain.repositories.email_verification_token import EmailVerificationTokenRepository
from reforma_authorization.infrastructure.rabbitmq.publisher import MailPublisher

class RegisterUseCase:
    def __init__(self, user_repo, email_token_repo, password_hasher, mail_publisher: MailPublisher):
        self.user_repo = user_repo
        self.email_token_repo = email_token_repo
        self.password_hasher = password_hasher
        self.mail_publisher = mail_publisher

    def execute(self, username: str, email: str, password: str):
        if self.user_repo.get_by_email(email):
            raise ValueError("User with this email already exists")
        if self.user_repo.get_by_username(username):
            raise ValueError("User with this username already exists")

        hashed_password = self.password_hasher.hash(password)
        user = self.user_repo.create(
            User(id=0, username=username, email=email, password_hash=hashed_password)
        )

        # создаём токен подтверждения email
        token_str = secrets.token_urlsafe(32)
        token = EmailVerificationToken(
            user_id=user.id,
            token=token_str,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        self.email_token_repo.save(token)

        # отправляем событие на Mail-service
        self.mail_publisher.send_email_verification(user.id, user.email, token.token)
        self.mail_publisher.close()

        return user
