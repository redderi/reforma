from typing import Optional, List
from uuid import UUID
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from reforma_survey.domain.entities.user_profile import UserProfile
from reforma_survey.domain.repositories.user_profile_repository import UserProfileRepository
from reforma_survey.infrastructure.db.models import UserProfileModel


class UserProfileRepositoryImpl(UserProfileRepository):

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: UUID) -> Optional[UserProfile]:
        result = await self.db.execute(
            select(UserProfileModel)
            .where(UserProfileModel.id == id)
            .options(
                selectinload(UserProfileModel.surveys),
                selectinload(UserProfileModel.templates),
                selectinload(UserProfileModel.reports),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_email(self, email: str) -> Optional[UserProfile]:
        result = await self.db.execute(
            select(UserProfileModel)
            .where(UserProfileModel.email == email)
            .options(
                selectinload(UserProfileModel.surveys),
                selectinload(UserProfileModel.templates),
                selectinload(UserProfileModel.reports),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_all(self) -> List[UserProfile]:
        result = await self.db.execute(select(UserProfileModel))
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def create(self, profile: UserProfile) -> UserProfile:
        model = UserProfileModel(
            id=profile.id,
            username=profile.username,
            email=profile.email,
            profile_picture=profile.profile_picture,
            bio=profile.bio,
            gender=profile.gender,
            birth_date=profile.birth_date,
            country=profile.country,
            city=profile.city,
        )
        self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)
        return self._to_entity(model)


    async def update_username(self, user_id: UUID, new_username: str) -> UserProfile:
        model = await self._get_model_or_raise(user_id)
        model.username = new_username
        await self.db.refresh(model)
        return self._to_entity(model)

    async def update_email(self, user_id: UUID, new_email: str) -> UserProfile:
        model = await self._get_model_or_raise(user_id)
        model.email = new_email
        await self.db.refresh(model)
        return self._to_entity(model)

    async def update_profile_picture(self, user_id: UUID, picture_url: str | None) -> UserProfile:
        model = await self._get_model_or_raise(user_id)
        model.profile_picture = picture_url
        await self.db.refresh(model)
        return self._to_entity(model)

    async def update_bio(self, user_id: UUID, bio: str | None) -> UserProfile:
        model = await self._get_model_or_raise(user_id)
        model.bio = bio
        await self.db.refresh(model)
        return self._to_entity(model)

    async def update_gender(self, user_id: UUID, gender: str | None) -> UserProfile:
        model = await self._get_model_or_raise(user_id)
        model.gender = gender
        await self.db.refresh(model)
        return self._to_entity(model)

    async def update_birth_date(self, user_id: UUID, birth_date: date | None) -> UserProfile:
        model = await self._get_model_or_raise(user_id)
        model.birth_date = birth_date
        await self.db.refresh(model)
        return self._to_entity(model)

    async def update_location(
        self,
        user_id: UUID,
        country: str | None,
        city: str | None,
    ) -> UserProfile:
        model = await self._get_model_or_raise(user_id)
        model.country = country
        model.city = city
        await self.db.refresh(model)
        return self._to_entity(model)

    async def delete(self, user_id: UUID) -> None:
        stmt = delete(UserProfileModel).where(UserProfileModel.id == user_id)
        await self.db.execute(stmt)

    async def _get_model_or_raise(self, user_id: UUID) -> UserProfileModel:
        model = await self.db.get(UserProfileModel, user_id)
        if not model:
            raise ValueError("UserProfile not found")
        return model

    def _to_entity(self, model: UserProfileModel) -> UserProfile:
        return UserProfile(
            id=model.id,
            username=model.username,
            email=model.email,
            profile_picture=model.profile_picture,
            bio=model.bio,
            gender=model.gender,
            birth_date=model.birth_date,
            country=model.country,
            city=model.city,
            surveys=[s.id for s in getattr(model, "surveys", [])],
            templates=[t.id for t in getattr(model, "templates", [])],
            reports=[r.id for r in getattr(model, "reports", [])],
        )
