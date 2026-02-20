from datetime import datetime
from uuid import UUID
from reforma_authorization.domain.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from reforma_authorization.domain.services.token_service import TokenService
from reforma_authorization.domain.entities.refresh_token import RefreshToken


class RefreshAccessTokenUseCase:
    def __init__(
        self, refresh_repo: RefreshTokenRepository, token_service: TokenService
    ):
        self.refresh_repo = refresh_repo
        self.token_service = token_service

    async def execute(self, refresh_token_str: str) -> dict:
        payload = self.token_service.decode_token(refresh_token_str)
        if not payload:
            raise ValueError("Invalid refresh-токен")
        if payload.get("type") != "refresh":
            raise ValueError("The provided token is not a refresh token")
        jti = payload.get("jti")
        if not jti:
            raise ValueError("JTI is missing from the refresh token.")
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise ValueError("Missing sub in refresh token")
        try:
            user_id = UUID(user_id_str)
        except ValueError:
            raise ValueError("Incorrect user_id format in token")
        device_id = payload.get("device_id")
        stored_token = await self.refresh_repo.get_by_jti(jti)
        if not stored_token:
            raise ValueError("Refresh token not found or already used")
        if stored_token.revoked:
            raise ValueError("Refresh token revoked")
        if stored_token.expires_at < datetime.utcnow():
            await self.refresh_repo.mark_revoked(jti)
            raise ValueError("Refresh token expired")
        await self.refresh_repo.mark_revoked(jti)
        new_refresh_str = self.token_service.create_refresh_token(
            user_id=user_id, device_id=device_id
        )
        new_payload = self.token_service.decode_token(new_refresh_str)
        if not new_payload:
            raise RuntimeError("Failed to decode the newly generated refresh token.")
        new_jti = new_payload["jti"]
        new_expires_at = datetime.fromtimestamp(new_payload["exp"])
        await self.refresh_repo.save(
            RefreshToken(
                token=new_refresh_str,
                jti=new_jti,
                user_id=user_id,
                device_id=device_id,
                expires_at=new_expires_at,
                revoked=False,
            )
        )
        access_token = self.token_service.create_access_token(
            user_id=user_id,
            user_role=payload.get("role", "user"),
            user_status=payload.get("status", "active"),
        )
        return {"access_token": access_token, "refresh_token": new_refresh_str}
