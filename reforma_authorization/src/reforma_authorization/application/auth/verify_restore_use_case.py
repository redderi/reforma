from reforma_authorization.domain.repositories.user_repository import UserRepository
from reforma_authorization.infrastructure.repositories.email_verification_token_impl import (
    EmailTokenRepositoryImpl,
)
from reforma_authorization.domain.entities.user import UserStatus


class VerifyRestoreUseCase:
    def __init__(self, user_repo: UserRepository, token_repo: EmailTokenRepositoryImpl):
        self.user_repo = user_repo
        self.token_repo = token_repo

    async def execute(self, token: str):
        token_obj = await self.token_repo.get(token)
        if not token_obj:
            raise ValueError("Invalid or expired token")
        user = await self.user_repo.get_by_id(token_obj.user_id)
        if not user:
            raise ValueError("User not found")
        if user.status != UserStatus.DEACTIVATED:
            raise ValueError("The user cannot be restored.")
        user.status = UserStatus.ACTIVE
        user.deleted_at = None
        await self.user_repo.update(user)
        await self.token_repo.delete(token_obj.token)
