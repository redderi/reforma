from abc import ABC, abstractmethod
from reforma_authorization.domain.entities.refresh_token import RefreshToken
from uuid import UUID


class RefreshTokenRepository(ABC):
    @abstractmethod
    async def save(self, token: RefreshToken) -> None:
        pass

    @abstractmethod
    async def get_by_jti(self, jti: str) -> RefreshToken | None:
        pass

    @abstractmethod
    async def mark_revoked(self, jti: str) -> bool:
        pass

    @abstractmethod
    async def delete_by_jti(self, jti: str) -> None:
        pass

    @abstractmethod
    async def delete_by_user_and_device(
        self, user_id: UUID, device_id: str
    ) -> None:
        pass

    @abstractmethod
    async def delete_all_by_user(self, user_id: UUID) -> None:
        pass
