from abc import ABC, abstractmethod
from typing import Optional
from reforma_survey.domain.entities.user_profile import UserProfile

class UserProfileRepository(ABC):

    @abstractmethod
    def get_by_id(self, id: str) -> UserProfile | None:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> UserProfile | None:
        pass

    @abstractmethod
    def create(self, user: UserProfile) -> UserProfile:
        pass

    @abstractmethod
    def update_username(self, user_id, new_username) -> UserProfile:
        pass

    @abstractmethod
    def update_email(self, user_id, new_email) -> UserProfile:
        pass

    @abstractmethod
    def delete(self, user_id) -> None:
        pass