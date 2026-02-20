from datetime import datetime
from reforma_authorization.domain.entities.refresh_token import RefreshToken
from reforma_authorization.domain.repositories.user_repository import UserRepository
from reforma_authorization.domain.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from reforma_authorization.domain.services.password_hasher import PasswordHasher
from reforma_authorization.domain.services.token_service import TokenService
from reforma_authorization.domain.entities.user import UserStatus


class LoginUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        refresh_repo: RefreshTokenRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ):
        self.user_repo = user_repo
        self.refresh_repo = refresh_repo
        self.password_hasher = password_hasher
        self.token_service = token_service

    async def execute(self, email: str, password: str, device_id: str) -> dict:
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise ValueError("Incorrect email or password")
        if not self.password_hasher.verify(password, user.password_hash):
            raise ValueError("Incorrect password")
        if not getattr(user, "is_email_verified", False):
            raise ValueError("Email is not confirmed. Please confirm your email")
        if user.status in [
            UserStatus.DEACTIVATED,
            UserStatus.SUSPENDED,
            UserStatus.DELETED,
        ]:
            raise ValueError(f"Access Denied. Account Status: {user.status.value}")
        await self.refresh_repo.delete_by_user_and_device(user.id, device_id)
        access_token = self.token_service.create_access_token(
            user_id=user.id, user_role=user.role, user_status=user.status
        )
        refresh_token_str = self.token_service.create_refresh_token(
            user_id=user.id, device_id=device_id
        )
        payload = self.token_service.decode_token(refresh_token_str)
        if not payload or "jti" not in payload or "exp" not in payload:
            raise RuntimeError("Failed to create refresh-токен")
        jti = payload["jti"]
        expires_at = datetime.fromtimestamp(payload["exp"])
        await self.refresh_repo.save(
            RefreshToken(
                token=refresh_token_str,
                jti=jti,
                user_id=user.id,
                device_id=device_id,
                expires_at=expires_at,
                revoked=False,
            )
        )
        return {"access_token": access_token, "refresh_token": refresh_token_str}
