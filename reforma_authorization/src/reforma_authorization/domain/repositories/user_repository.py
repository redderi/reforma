from abc import ABC, abstractmethod
from reforma_authorization.domain.entities.user import User

class UserRepository(ABC):

    @abstractmethod
    def get_by_id(self, id: int) -> User | None:
        pass

    @abstractmethod
    def get_by_username(self, username: str) -> User | None:
        pass                            

    @abstractmethod
    def get_by_email(self, email: str) -> User | None:
        pass

    @abstractmethod
    def create(self, user: User) -> User:
        pass

    @abstractmethod
    def change_email(self, user: User, new_email: str) -> User:
        pass

    @abstractmethod
    def change_username(self, user: User, new_username: str) -> User:
        pass

    @abstractmethod
    def change_password(self, user: User, new_password_hash: str) -> User:
        pass

    @abstractmethod
    def delete(self, user: User) -> None:
        pass
    
    @abstractmethod
    def mark_email_as_verified(self, user_id: int):
        pass
