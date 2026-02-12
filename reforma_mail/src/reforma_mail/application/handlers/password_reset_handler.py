from reforma_mail.domain.entities.email_message import EmailMessage
from reforma_mail.application.send_email_use_case import SendEmailUseCase
from reforma_mail.infrastructure.mail.smtp_service import SMTPService


class PasswordResetHandler:

    def handle(self, payload: dict):
        reset_url = f"http://localhost:8000/auth/reset_password?token={payload['token']}"

        message = EmailMessage(
            to_email=payload["email"],
            subject="Сброс пароля",
            template="reset_password.html",
            context={
                "username": payload["username"],
                "reset_url": reset_url
            }
        )

        SendEmailUseCase(SMTPService()).execute(message)
