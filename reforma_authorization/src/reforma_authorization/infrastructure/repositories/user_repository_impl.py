from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from reforma_authorization.domain.repositories.user_repository import UserRepository
from reforma_authorization.domain.entities.user import User, UserStatus
from reforma_authorization.infrastructure.db.models import UserModel


class UserRepositoryImpl(UserRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_entity(self, model: UserModel) -> User:
        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            role=model.role,
            password_hash=model.password_hash,
            is_email_verified=model.is_email_verified,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
            suspended_at=model.suspended_at,
            suspension_reason=model.suspension_reason,
            suspended_by=model.suspended_by
        )

    async def get_by_id(self, id: UUID) -> User | None:
        stmt = select(UserModel).where(
            UserModel.id == id,
            #UserModel.deleted_at.is_(None)
        )
        result = await self.db.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(UserModel).where(
            UserModel.username == username,
           # UserModel.deleted_at.is_(None)
        )
        result = await self.db.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(
            UserModel.email == email,
            #UserModel.deleted_at.is_(None)
        )
        result = await self.db.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, user: User) -> User:
        model = UserModel(
            id=user.id,
            username=user.username,
            email=user.email,
            password_hash=user.password_hash,
            role=user.role,
            is_email_verified=user.is_email_verified,
            status=user.status
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

    # ----------------- Soft Delete -----------------
    async def delete(self, user: User) -> None:
        """Soft delete по объекту User"""
        model = await self.db.get(UserModel, user.id)
        if not model:
            raise ValueError("User not found")
        model.deleted_at = datetime.utcnow()
        model.status = UserStatus.DELETED
        await self.db.commit()

    async def delete_by_id(self, user_id: UUID) -> None:
        model = await self.db.get(UserModel, user_id)
        if not model:
            raise ValueError("User not found")
        model.deleted_at = datetime.utcnow()
        model.status = UserStatus.DELETED
        await self.db.commit()

    # ----------------- Hard Delete -----------------
    async def hard_delete(self, user: User) -> None:
        model = await self.db.get(UserModel, user.id)
        if not model:
            raise ValueError("User not found")
        await self.db.delete(model)
        await self.db.commit()

    async def hard_delete_by_id(self, user_id: UUID) -> None:
        model = await self.db.get(UserModel, user_id)
        if not model:
            raise ValueError("User not found")
        await self.db.delete(model)
        await self.db.commit()

    async def mark_email_as_verified(self, user_id: UUID):
        model = await self.db.get(UserModel, user_id)
        if not model:
            raise ValueError("User not found")

        model.is_email_verified = True
        if model.status == UserStatus.REGISTERED:
            model.status = UserStatus.ACTIVE

        await self.db.commit()
        await self.db.refresh(model)

    async def update(self, user: User) -> User:
        model = await self.db.get(UserModel, user.id)
        if not model:
            raise ValueError("User not found")

        model.username = user.username
        model.email = user.email
        model.password_hash = user.password_hash
        model.role = user.role
        model.is_email_verified = user.is_email_verified
        model.status = user.status
        model.suspended_at = user.suspended_at
        model.suspension_reason = user.suspension_reason
        model.suspended_by = user.suspended_by
        model.deleted_at = user.deleted_at

        await self.db.commit()
        await self.db.refresh(model)
        return self._to_entity(model)

    async def get_all(self, include_deleted: bool = False) -> list[User]:
        stmt = select(UserModel)
        if not include_deleted:
            pass
            #stmt = stmt.where(UserModel.deleted_at.is_(None))

        result = await self.db.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_by_status(self, status: UserStatus) -> list[User]:
        stmt = select(UserModel).where(
            UserModel.status == status,
            UserModel.deleted_at.is_(None)
        )
        result = await self.db.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def activate(self, user: User) -> User:
        model = await self.db.get(UserModel, user.id)
        if not model:
            raise ValueError("User not found")
        model.status = UserStatus.ACTIVE
        model.deleted_at = None
        await self.db.commit()
        await self.db.refresh(model)
        return self._to_entity(model)

    async def deactivate(self, user: User) -> User:
        model = await self.db.get(UserModel, user.id)
        if not model:
            raise ValueError("User not found")
        model.status = UserStatus.DEACTIVATED
        await self.db.commit()
        await self.db.refresh(model)
        return self._to_entity(model)

    async def suspend(self, user: User, reason: str, suspended_by: UUID) -> User:
        model = await self.db.get(UserModel, user.id)
        if not model:
            raise ValueError("User not found")
        model.status = UserStatus.SUSPENDED
        model.suspension_reason = reason
        model.suspended_by = suspended_by
        model.suspended_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(model)
        return self._to_entity(model)

    async def restore(self, user: User) -> User:
        model = await self.db.get(UserModel, user.id)
        if not model:
            raise ValueError("User not found")
        model.status = UserStatus.DEACTIVATED
        model.deleted_at = None
        await self.db.commit()
        await self.db.refresh(model)
        return self._to_entity(model)
