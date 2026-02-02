from reforma_authorization.domain.repositories.user_repository import UserRepository
from reforma_authorization.domain.repositories.refresh_token_repository import RefreshTokenRepository

class DeleteUserUseCase():

    def __init__(self, user_repo: UserRepository, refresh_token_repo: RefreshTokenRepository):
        self.user_repo = user_repo
        self.refresh_token_repo = refresh_token_repo

    def execute(self, user_id: int) -> None:
        user = self.user_repo.get_by_id(user_id)

        if not user:
            raise ValueError("User not found")

        self.refresh_token_repo.delete_all_by_user(user_id)

        self.user_repo.delete(user)