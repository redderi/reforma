from datetime import datetime, timedelta
from reforma_authorization.domain.entities.refresh_token import RefreshToken
from reforma_authorization.domain.repositories.user_repository import UserRepository
from reforma_authorization.domain.repositories.refresh_token_repository import RefreshTokenRepository
from reforma_authorization.domain.services.password_hasher import PasswordHasher
from reforma_authorization.domain.services.token_service import TokenService

class LoginUseCase:

    def __init__(
        self,
        user_repo: UserRepository,
        refresh_repo: RefreshTokenRepository,
        hasher: PasswordHasher,
        token_service: TokenService
    ):
        self.user_repo = user_repo
        self.refresh_repo = refresh_repo
        self.hasher = hasher
        self.token_service = token_service

    def execute(self, email: str, password: str, device_id: str) -> dict:
        user = self.user_repo.get_by_email(email)

        if not user:
            raise ValueError("Invalid user")
        if not self.hasher.verify(password, user.password_hash):
            raise ValueError("Invalid password")
        
        if not getattr(user, "is_email_verified", False):
            raise ValueError("Email not verified. Please confirm your email before logging in.")

        self.refresh_repo.delete_by_user_and_device(user.id, device_id)

        access_token = self.token_service.create_access_token(user.id)
        refresh_token = self.token_service.create_refresh_token()

        self.refresh_repo.save(
            RefreshToken(
                token=refresh_token,
                user_id=user.id,
                device_id=device_id,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
