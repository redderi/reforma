from reforma_mail.domain.entities.email_message import EmailMessage
from reforma_mail.application.send_email_use_case import SendEmailUseCase
from reforma_mail.infrastructure.mail.smtp_service import SMTPService
from reforma_mail.common.logger import log_info

class EmailVerificationHandler:

    def handle(self, payload: dict):
        verify_url = f"http://localhost/api/auth_service/auth/verify_email?token={payload['token']}"

        message = EmailMessage(
            to_email=payload["email"],
            subject="Подтверждение email",
            template="verify_email.html",
            context={
                "username": payload["username"],
                "verify_url": verify_url
            }
        )
        log_info(f"EmailVerificationHandler verify url={verify_url}", service="mail-service")
        #SendEmailUseCase(SMTPService()).execute(message)
