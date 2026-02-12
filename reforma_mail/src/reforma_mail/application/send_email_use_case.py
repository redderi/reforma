from reforma_mail.domain.repositories.mail_repository import MailRepository
from reforma_mail.domain.entities.email_message import EmailMessage


class SendEmailUseCase:

    def __init__(self, repo: MailRepository):
        self.repo = repo

    def execute(self, message: EmailMessage):
        self.repo.send(message)
