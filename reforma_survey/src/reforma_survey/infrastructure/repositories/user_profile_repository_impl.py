from typing import List
from uuid import UUID
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from reforma_survey.domain.entities.user_profile import UserProfile
from reforma_survey.domain.repositories.user_profile_repository import (
    UserProfileRepository,
)
from reforma_survey.infrastructure.db.models import UserProfileModel


class UserProfileRepositoryImpl(UserProfileRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: UUID) -> UserProfile | None:
        result = await self.db.execute(
            select(UserProfileModel)
            .where(UserProfileModel.id == id)
            .options(
                selectinload(UserProfileModel.surveys),
                selectinload(UserProfileModel.templates),
                selectinload(UserProfileModel.reports),
                selectinload(UserProfileModel.responses),
            )
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model, load_collections=True)

    async def get_by_email(self, email: str) -> UserProfile | None:
        result = await self.db.execute(
            select(UserProfileModel)
            .where(UserProfileModel.email == email)
            .options(
                selectinload(UserProfileModel.surveys),
                selectinload(UserProfileModel.templates),
                selectinload(UserProfileModel.reports),
                selectinload(UserProfileModel.responses),
            )
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model, load_collections=True)

    async def get_all(self) -> List[UserProfile]:
        result = await self.db.execute(
            select(UserProfileModel).options(
                selectinload(UserProfileModel.surveys),
                selectinload(UserProfileModel.templates),
                selectinload(UserProfileModel.reports),
                selectinload(UserProfileModel.responses),
            )
        )
        models = result.scalars().all()
        return [self._to_entity(model, load_collections=True) for model in models]

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
            balance=profile.balance,
        )
        self.db.add(model)
        await self.db.flush()
        await self.db.commit()
        return self._to_entity(model)

    async def update_username(self, user_id: UUID, new_username: str) -> UserProfile:
        model = await self._get_model_or_raise(user_id)
        model.username = new_username
        await self.db.flush()
        await self.db.commit()
        return self._to_entity(model)

    async def update_email(self, user_id: UUID, new_email: str) -> UserProfile:
        model = await self._get_model_or_raise(user_id)
        model.email = new_email
        await self.db.flush()
        await self.db.commit()
        return self._to_entity(model)

    async def update_profile_picture(
        self, user_id: UUID, picture_url: str | None
    ) -> UserProfile:
        model = await self._get_model_or_raise(user_id)
        model.profile_picture = picture_url
        await self.db.flush()
        await self.db.commit()
        return self._to_entity(model)

    async def update_bio(self, user_id: UUID, bio: str | None) -> UserProfile:
        model = await self._get_model_or_raise(user_id)
        model.bio = bio
        await self.db.flush()
        await self.db.commit()
        return self._to_entity(model)

    async def update_gender(self, user_id: UUID, gender: str | None) -> UserProfile:
        model = await self._get_model_or_raise(user_id)
        model.gender = gender
        await self.db.flush()
        await self.db.commit()
        return self._to_entity(model)

    async def update_birth_date(
        self, user_id: UUID, birth_date: date | None
    ) -> UserProfile:
        model = await self._get_model_or_raise(user_id)
        model.birth_date = birth_date
        await self.db.flush()
        await self.db.commit()
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
        await self.db.flush()
        await self.db.commit()
        return self._to_entity(model)

    async def delete(self, user_id: UUID) -> None:
        stmt = delete(UserProfileModel).where(UserProfileModel.id == user_id)
        await self.db.execute(stmt)

    async def update_balance(self, user_id: UUID, balance: int) -> UserProfile:
        model = await self._get_model_or_raise(user_id)
        model.balance = balance
        await self.db.flush()
        await self.db.commit()
        return self._to_entity(model)

    async def add_balance(self, user_id: UUID, amount: int) -> UserProfile:
        model = await self._get_model_or_raise(user_id)
        model.balance = (model.balance or 0) + amount
        await self.db.flush()
        await self.db.commit()
        return self._to_entity(model)

    async def _get_model_or_raise(self, user_id: UUID) -> UserProfileModel:
        model = await self.db.get(UserProfileModel, user_id)
        if not model:
            raise ValueError(f"UserProfile with id {user_id} not found")
        return model

    def _to_entity(
        self, model: UserProfileModel, load_collections: bool = False
    ) -> UserProfile:
        surveys = []
        templates = []
        reports = []
        responses = []

        if load_collections:
            surveys = [s.id for s in model.surveys]
            templates = [t.id for t in model.templates]
            reports = [r.id for r in model.reports]
            responses = [r.id for r in model.responses]

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
            surveys=surveys,
            templates=templates,
            reports=reports,
            responses=responses,
            balance=model.balance,
        )
