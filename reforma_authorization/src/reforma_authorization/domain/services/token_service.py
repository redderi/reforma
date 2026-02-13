from abc import ABC, abstractmethod
import uuid

class TokenService(ABC):

    @abstractmethod
    def create_access_token(self, user_id: uuid.UUID) -> str:
        pass

    @abstractmethod
    def create_refresh_token(self) -> str:
        pass
    
    @abstractmethod
    def decode_access_token(self, token: str) -> dict | None:
        pass