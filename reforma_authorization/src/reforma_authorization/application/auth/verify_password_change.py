from reforma_authorization.domain.repositories.user_repository import UserRepository
from reforma_authorization.infrastructure.repositories.email_verification_token_impl import EmailTokenRepositoryImpl
from reforma_authorization.infrastructure.repositories.refresh_token_repository_impl import RefreshTokenRepositoryImpl
from reforma_common.logger import log_info

class VerifyPasswordChangeUseCase:
    def __init__(self, user_repo: UserRepository, token_repo: EmailTokenRepositoryImpl, refresh_repo: RefreshTokenRepositoryImpl):
        self.user_repo = user_repo
        self.token_repo = token_repo
        self.refresh_repo = refresh_repo

    async def execute(self, token: str):
        token_obj = await self.token_repo.get(token)
        if not token_obj:
            raise ValueError("Неверный или просроченный токен")

        user = await self.user_repo.get_by_id(token_obj.user_id)
        if not user:
            raise ValueError("Пользователь не найден")

        new_password_hash = token_obj.data.get("new_password_hash")
        if not new_password_hash:
            raise ValueError("Новый пароль отсутствует в токене")

        await self.user_repo.change_password(user, new_password_hash)
        await self.refresh_repo.delete_all_by_user(user.id)
        await self.token_repo.delete(token_obj.token)
        log_info(f"Password changed successfully for user_id={user.id}", service="auth-service")
        return {"message": "Пароль успешно изменён"}
