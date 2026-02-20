from reforma_mail.domain.entities.email_message import EmailMessage
from reforma_common.logger import log_info


class UserRestoreHandler:
    async def handle(self, payload: dict):
        verify_url = f"http://localhost/api/auth_service/auth/verify_restore?token={payload['token']}"
        message = EmailMessage(
            to_email=payload["email"],
            subject="Подтверждение email",
            template="user_restore.html",
            context={"username": payload["username"], "verify_url": verify_url},
        )
        log_info(
            f"EmailVerificationHandler verify url={verify_url}", service="mail-service"
        )
        # await SendEmailUseCase(SMTPService()).execute(message)
