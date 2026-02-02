from reforma_authorization.domain.repositories.refresh_token_repository import RefreshTokenRepository

class LogoutUseCase:

    def __init__(self, refresh_repo: RefreshTokenRepository):
        self.refresh_repo = refresh_repo

    def execute(self, refresh_token: str) -> None:
        self.refresh_repo.delete(refresh_token)