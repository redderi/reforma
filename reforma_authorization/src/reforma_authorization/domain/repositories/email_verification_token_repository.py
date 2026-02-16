from abc import ABC, abstractmethod
from reforma_authorization.domain.entities.email_verification_token import EmailVerificationToken
import uuid

class EmailVerificationTokenRepository(ABC):

    @abstractmethod
    async def save(self, token: EmailVerificationToken):
        pass
    
    @abstractmethod
    async def get(self, token: str) -> EmailVerificationToken | None:
        pass

    @abstractmethod
    async def delete(self, token: str):
        pass

    @abstractmethod
    async def create_token(self, user_id: uuid.UUID, hours_valid: int, data: dict):
        pass