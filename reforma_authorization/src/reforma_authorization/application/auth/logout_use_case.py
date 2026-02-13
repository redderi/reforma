from reforma_authorization.domain.repositories.refresh_token_repository import RefreshTokenRepository

class LogoutUseCase:

    def __init__(self, refresh_repo: RefreshTokenRepository):
        self.refresh_repo = refresh_repo

    async def execute(self, refresh_token: str) -> None:
        token_obj = await self.refresh_repo.get(refresh_token)
        if not token_obj:
            raise ValueError("Refresh token not found or expired")
        
        await self.refresh_repo.delete(refresh_token)
