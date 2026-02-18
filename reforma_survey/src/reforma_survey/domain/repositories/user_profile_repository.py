from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from datetime import date

from reforma_survey.domain.entities.user_profile import UserProfile


class UserProfileRepository(ABC):

    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional[UserProfile]:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[UserProfile]:
        pass

    @abstractmethod
    async def get_all(self) -> List[UserProfile]:
        pass

    @abstractmethod
    async def create(self, user: UserProfile) -> UserProfile:
        pass

    @abstractmethod
    async def update_username(self, user_id: UUID, new_username: str) -> UserProfile:
        pass

    @abstractmethod
    async def update_email(self, user_id: UUID, new_email: str) -> UserProfile:
        pass

    @abstractmethod
    async def update_profile_picture(self, user_id: UUID, picture_url: str | None) -> UserProfile:
        pass

    @abstractmethod
    async def update_bio(self, user_id: UUID, bio: str | None) -> UserProfile:
        pass

    @abstractmethod
    async def update_gender(self, user_id: UUID, gender: str | None) -> UserProfile:
        pass

    @abstractmethod
    async def update_birth_date(self, user_id: UUID, birth_date: date | None) -> UserProfile:
        pass

    @abstractmethod
    async def update_location(
        self,
        user_id: UUID,
        country: str | None,
        city: str | None
    ) -> UserProfile:
        pass

    @abstractmethod
    async def update_balance(self, user_id: UUID, balance: int) -> UserProfile:
        pass

    @abstractmethod
    async def add_balance(self, user_id: UUID, amount: int) -> UserProfile:
        pass
    
    @abstractmethod
    async def delete(self, user_id: UUID) -> None:
        pass
