from uuid import UUID
from reforma_authorization.domain.repositories.user_repository import UserRepository
from reforma_authorization.infrastructure.repositories.email_verification_token_impl import EmailTokenRepositoryImpl
from reforma_common.logger import log_info, log_warning

class VerifyEmailUseCase:
    def __init__(self, user_repo: UserRepository, token_repo: EmailTokenRepositoryImpl):
        self.user_repo = user_repo
        self.token_repo = token_repo

    async def execute(self, token: str):
        token_obj = await self.token_repo.get(token)
        if not token_obj:
            log_warning(f"Invalid or expired email verification token: {token}", service="auth-service")
            raise ValueError("Неверный или просроченный токен")

        user = await self.user_repo.get_by_id(token_obj.user_id)
        if not user:
            raise ValueError("Пользователь не найден")

        await self.user_repo.mark_email_as_verified(user.id)

        await self.token_repo.delete(token_obj.token)
        log_info(f"Email verified successfully for user_id={user.id}", service="auth-service")
        return {"message": "Email успешно подтверждён"}
