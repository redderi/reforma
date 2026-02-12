from abc import ABC, abstractmethod
from reforma_authorization.domain.entities.email_verification_token import EmailVerificationToken

class EmailVerificationTokenRepository(ABC):

    @abstractmethod
    def save(self, token: EmailVerificationToken):
        pass
    
    @abstractmethod
    def get(self, token: str) -> EmailVerificationToken | None:
        pass

    @abstractmethod
    def delete(self, token: str):
        pass

    @abstractmethod
    def create_token(self, user_id: int, hours_valid: int):
        pass