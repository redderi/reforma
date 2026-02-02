from abc import ABC, abstractmethod

class TokenService(ABC):

    @abstractmethod
    def create_access_token(self, user_id: int) -> str:
        pass

    @abstractmethod
    def create_refresh_token(self) -> str:
        pass
    
    @abstractmethod
    def decode_access_token(self, token: str) -> dict | None:
        pass