from abc import ABC, abstractmethod
from reforma_authorization.domain.entities.user import User, UserStatus
from uuid import UUID


class UserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: UUID) -> User | None:
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        pass

    @abstractmethod
    async def create(self, user: User) -> User:
        pass

    @abstractmethod
    async def change_email(self, user: User, new_email: str) -> User:
        pass

    @abstractmethod
    async def change_username(self, user: User, new_username: str) -> User:
        pass

    @abstractmethod
    async def change_password(self, user: User, new_password_hash: str) -> User:
        pass

    @abstractmethod
    async def update(self, user: User) -> User:
        pass

    @abstractmethod
    async def delete(self, user: User) -> None:
        pass

    @abstractmethod
    async def delete_by_id(self, user_id: UUID) -> None:
        pass

    @abstractmethod
    async def mark_email_as_verified(self, user_id: UUID) -> None:
        pass

    @abstractmethod
    async def get_all(self, include_deleted: bool = False) -> list[User]:
        pass

    @abstractmethod
    async def activate(self, user: User) -> User:
        pass

    @abstractmethod
    async def deactivate(self, user: User) -> User:
        pass

    @abstractmethod
    async def suspend(self, user: User, reason: str, suspended_by: UUID) -> User:
        pass

    @abstractmethod
    async def restore(self, user: User) -> User:
        pass

    @abstractmethod
    async def get_by_status(self, status: UserStatus) -> list[User]:
        pass

    @abstractmethod
    async def hard_delete(self, user: User) -> None:
        pass

    @abstractmethod
    async def hard_delete_by_id(self, user_id: UUID) -> None:
        pass
