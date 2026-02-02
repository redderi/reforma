from reforma_authorization.domain.repositories.refresh_token_repository import RefreshTokenRepository
from reforma_authorization.domain.services.token_service import TokenService

from datetime import datetime, timedelta
from reforma_authorization.domain.entities.refresh_token import RefreshToken

class RefreshAccessTokenUseCase:

    def __init__(self, refresh_repo: RefreshTokenRepository, token_service: TokenService):
        self.refresh_repo = refresh_repo
        self.token_service = token_service

    def execute(self, refresh_token: str) -> dict:
        token = self.refresh_repo.get(refresh_token)
        if not token:
            raise ValueError("Invalid refresh token")

        self.refresh_repo.delete(refresh_token)

        new_refresh = self.token_service.create_refresh_token()

        self.refresh_repo.save(
            RefreshToken(
                token=new_refresh,
                user_id=token.user_id,
                device_id=token.device_id,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
        )

        access = self.token_service.create_access_token(token.user_id)

        return {
            "access_token": access,
            "refresh_token": new_refresh
        }
