from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from reforma_authorization.domain.repositories.user_repository import UserRepository
from reforma_authorization.domain.entities.user import User
from reforma_authorization.infrastructure.db.models import UserModel
from sqlalchemy import delete


class UserRepositoryImpl(UserRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_entity(self, model: UserModel) -> User:
        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            password_hash=model.password_hash,
            is_email_verified=model.is_email_verified
        )

    async def get_by_id(self, id: UUID) -> User | None:
        model = await self.db.get(UserModel, id)
        return self._to_entity(model) if model else None

    async def get_by_username(self, username: str) -> User | None:
        result = await self.db.execute(
            select(UserModel).filter_by(username=username)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.db.execute(stmt)
        model = result.scalars().first()
        return self._to_entity(model) if model else None


    async def create(self, user: User) -> User:
        model = UserModel(
            id=user.id,
            username=user.username,
            email=user.email,
            password_hash=user.password_hash,
            is_email_verified=user.is_email_verified
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return self._to_entity(model)

    async def change_email(self, user: User, new_email: str) -> User:
        model = await self.db.get(UserModel, user.id)
        if not model:
            raise ValueError("User not found")

        model.email = new_email
        await self.db.commit()
        await self.db.refresh(model)
        return self._to_entity(model)

    async def change_username(self, user: User, new_username: str) -> User:
        model = await self.db.get(UserModel, user.id)
        if not model:
            raise ValueError("User not found")

        model.username = new_username
        await self.db.commit()
        await self.db.refresh(model)
        return self._to_entity(model)

    async def change_password(self, user: User, new_password_hash: str) -> User:
        model = await self.db.get(UserModel, user.id)
        if not model:
            raise ValueError("User not found")

        model.password_hash = new_password_hash
        await self.db.commit()
        await self.db.refresh(model)
        return self._to_entity(model)

    async def delete(self, user: User) -> None:
        stmt = delete(UserModel).where(UserModel.id == user.id)
        await self.db.execute(stmt)
        await self.db.commit()

    async def mark_email_as_verified(self, user_id: UUID):
        model = await self.db.get(UserModel, user_id)
        if not model:
            raise ValueError("User not found")

        model.is_email_verified = True
        await self.db.commit()
        await self.db.refresh(model)
