from abc import ABC, abstractmethod
from reforma_authorization.domain.entities.refresh_token import RefreshToken
import uuid

class RefreshTokenRepository(ABC):

    @abstractmethod
    def save(self, token:RefreshToken) -> None:
        pass

    @abstractmethod
    def get(self, token: str) -> RefreshToken | None:
        pass

    @abstractmethod
    def delete(self, token: str) -> None:
        pass

    @abstractmethod
    def delete_by_user_and_device(self, user_id: uuid.UUID, device_id: str) -> None:
        pass
    
    @abstractmethod
    def delete_all_by_user(self, user_id: uuid.UUID) -> None:
        pass