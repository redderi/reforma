from reforma_common.logger import log_info
from reforma_mail.domain.entities.email_message import EmailMessage


class PasswordChangeHandler:
    async def handle(self, payload: dict):
        reset_url = f"http://localhost/api/auth_service/user/change/verify_password_change?token={payload['token']}"
        message = EmailMessage(
            to_email=payload["email"],
            subject="Подтверждение смены пароля",
            template="change_password.html",
            context={"username": payload["username"], "verify_url": reset_url},
        )
        log_info(
            f"PasswordChangeHandler verify url={reset_url}", service="mail-service"
        )
        # await SendEmailUseCase(SMTPService()).execute(message)
