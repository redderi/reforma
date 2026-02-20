from datetime import datetime
from typing import Optional

from reforma_authorization.domain.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from reforma_authorization.infrastructure.security.jwt_service import JWTService


class LogoutUseCase:
    def __init__(self, refresh_repo: RefreshTokenRepository, token_service: JWTService):
        self.refresh_repo = refresh_repo
        self.token_service = token_service

    async def execute(self, refresh_token_str: str) -> bool:
        payload: Optional[dict] = self.token_service.decode_token(refresh_token_str)
        if not payload:
            return False
        if payload.get("type") != "refresh":
            return False
        jti: Optional[str] = payload.get("jti")
        if not jti:
            return False
        token_obj = await self.refresh_repo.get_by_jti(jti)
        if not token_obj:
            return True
        if token_obj.revoked:
            return True
        if token_obj.expires_at < datetime.utcnow():
            return True
        await self.refresh_repo.mark_revoked(jti)
        return True
