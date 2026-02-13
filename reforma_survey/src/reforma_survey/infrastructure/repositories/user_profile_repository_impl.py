from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from reforma_survey.domain.entities.user_profile import UserProfile
from reforma_survey.domain.repositories.user_profile_repository import UserProfileRepository
from reforma_survey.infrastructure.db.models import UserProfileModel
from sqlalchemy.orm import selectinload
from sqlalchemy import delete

class UserProfileRepositoryImpl(UserProfileRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: UUID) -> Optional[UserProfile]:
        result = await self.db.execute(select(UserProfileModel).where(UserProfileModel.id == id).options(
            selectinload(UserProfileModel.surveys),
            selectinload(UserProfileModel.templates),
            selectinload(UserProfileModel.reports),
        ))
        model: UserProfileModel | None = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def get_by_email(self, email: str) -> Optional[UserProfile]:
        result = await self.db.execute(select(UserProfileModel).where(UserProfileModel.email == email).options(
            selectinload(UserProfileModel.surveys),
            selectinload(UserProfileModel.templates),
            selectinload(UserProfileModel.reports),
        ))
        model: UserProfileModel | None = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def create(self, profile: UserProfile):
        model = UserProfileModel(
            id=profile.id,
            username=profile.username,
            email=profile.email,
            profile_picture=profile.profile_picture,
            bio=profile.bio
        )
        self.db.add(model)
        return self._to_entity(model)

    async def delete(self, user_id: UUID):
        stmt = delete(UserProfileModel).where(UserProfileModel.id == user_id)
        await self.db.execute(stmt)
        await self.db.commit()

    async def update_username(self, user_id: UUID, new_username: str):
        model = await self.db.get(UserProfileModel, user_id)  
        if model:
            model.username = new_username
            self.db.add(model) 
            await self.db.flush()

    async def update_email(self, user_id: UUID, new_email: str):
        model = await self.db.get(UserProfileModel, user_id)
        if model:
            model.email = new_email
            self.db.add(model)
            await self.db.flush()

    def _to_entity(self, model: UserProfileModel) -> UserProfile:
        return UserProfile(
            id=model.id,
            username=model.username,
            email=model.email,
            profile_picture=model.profile_picture,
            bio=model.bio,
            surveys=[s.id for s in getattr(model, "surveys", [])],
            templates=[t.id for t in getattr(model, "templates", [])],
            reports=[r.id for r in getattr(model, "reports", [])]
        )
