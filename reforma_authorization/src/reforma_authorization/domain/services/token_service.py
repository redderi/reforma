from abc import ABC, abstractmethod
from uuid import UUID


class TokenService(ABC):
    @abstractmethod
    def create_access_token(
        self, user_id: UUID, user_role: str, user_status: str
    ) -> str:
        pass

    @abstractmethod
    def create_refresh_token(self, user_id: UUID, device_id: str | None = None) -> str:
        pass

    @abstractmethod
    def decode_token(self, token: str) -> dict | None:
        pass
