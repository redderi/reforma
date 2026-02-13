from datetime import datetime
from uuid import UUID
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from reforma_authorization.domain.repositories.refresh_token_repository import RefreshTokenRepository
from reforma_authorization.domain.entities.refresh_token import RefreshToken
from reforma_authorization.infrastructure.db.models import RefreshTokenModel


class RefreshTokenRepositoryImpl(RefreshTokenRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_entity(self, model: RefreshTokenModel) -> RefreshToken:
        return RefreshToken(
            token=model.token,
            user_id=model.user_id,
            device_id=model.device_id,
            expires_at=model.expires_at,
        )

    async def save(self, token: RefreshToken) -> RefreshToken:
        model = RefreshTokenModel(
            token=token.token,
            user_id=token.user_id,
            device_id=token.device_id,
            expires_at=token.expires_at,
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return self._to_entity(model)

    async def delete(self, token: str) -> None:
        result = await self.db.execute(
            select(RefreshTokenModel).filter_by(token=token)
        )
        model = result.scalar_one_or_none()
        if model:
            await self.db.delete(model)
            await self.db.commit()

    async def delete_by_user_and_device(self, user_id: UUID, device_id: str) -> None:
        result = await self.db.execute(
            select(RefreshTokenModel).filter_by(user_id=user_id, device_id=device_id)
        )
        tokens = result.scalars().all()
        for model in tokens:
            await self.db.delete(model)
        await self.db.commit()

    async def delete_all_by_user(self, user_id: UUID) -> None:
        result = await self.db.execute(
            select(RefreshTokenModel).filter_by(user_id=user_id)
        )
        tokens = result.scalars().all()
        for model in tokens:
            await self.db.delete(model)
        await self.db.commit()

    async def get(self, token: str) -> RefreshToken | None:
        result = await self.db.execute(
            select(RefreshTokenModel).filter_by(token=token)
        )
        model = result.scalar_one_or_none()
        if not model or model.expires_at < datetime.utcnow():
            return None
        return self._to_entity(model)
