from reforma_authorization.domain.repositories.user_repository import UserRepository
from reforma_authorization.domain.services.password_hasher import PasswordHasher
from reforma_authorization.domain.repositories.refresh_token_repository import RefreshTokenRepository

class ChangePasswordUseCase:

    def __init__(self, user_repo:UserRepository, refresh_token_repo:RefreshTokenRepository,  password_hasher: PasswordHasher):
        self.user_repo = user_repo
        self.refresh_token_repo = refresh_token_repo
        self.password_hasher = password_hasher

    def execute(self, user_id: int, old_password: str, new_password: str):
        user = self.user_repo.get_by_id(user_id)

        if not user:
            raise ValueError("User not found")

        if not self.password_hasher.verify(old_password, user.password_hash):
            raise ValueError("Wrong old password")

        new_hash = self.password_hasher.hash(new_password)
        self.user_repo.change_password(user, new_hash)
        self.refresh_token_repo.delete_all_by_user(user_id)