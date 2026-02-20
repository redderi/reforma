from abc import ABC, abstractmethod
from reforma_mail.domain.entities.email_message import EmailMessage


class MailRepository(ABC):
    @abstractmethod
    def send(self, message: EmailMessage) -> None:
        pass
