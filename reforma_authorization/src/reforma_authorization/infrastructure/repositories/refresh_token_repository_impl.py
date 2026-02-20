from datetime import datetime
from uuid import UUID
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from reforma_authorization.domain.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from reforma_authorization.domain.entities.refresh_token import RefreshToken
from reforma_authorization.infrastructure.db.models import RefreshTokenModel


class RefreshTokenRepositoryImpl(RefreshTokenRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_entity(self, model: RefreshTokenModel) -> RefreshToken:
        return RefreshToken(
            token=model.token,
            jti=model.jti,
            user_id=model.user_id,
            device_id=model.device_id,
            expires_at=model.expires_at,
            revoked=model.revoked,
        )

    async def save(self, token: RefreshToken) -> None:
        stmt = (
            insert(RefreshTokenModel)
            .values(
                jti=token.jti,
                token=token.token,
                user_id=token.user_id,
                device_id=token.device_id,
                expires_at=token.expires_at,
                revoked=token.revoked,
            )
            .on_conflict_do_update(
                index_elements=["jti"],
                set_={
                    "token": token.token,
                    "user_id": token.user_id,
                    "device_id": token.device_id,
                    "expires_at": token.expires_at,
                    "revoked": token.revoked,
                },
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def get_by_jti(self, jti: str) -> RefreshToken | None:
        result = await self.db.execute(select(RefreshTokenModel).filter_by(jti=jti))
        model = result.scalar_one_or_none()
        if not model:
            return None
        if model.expires_at < datetime.utcnow() or model.revoked:
            return None
        return self._to_entity(model)

    async def mark_revoked(self, jti: str) -> bool:
        stmt = (
            update(RefreshTokenModel)
            .where(RefreshTokenModel.jti == jti)
            .values(revoked=True)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

    async def delete_by_jti(self, jti: str) -> None:
        stmt = sa.delete(RefreshTokenModel).where(RefreshTokenModel.jti == jti)
        await self.db.execute(stmt)
        await self.db.commit()

    async def delete_by_user_and_device(self, user_id: UUID, device_id: str) -> None:
        stmt = sa.delete(RefreshTokenModel).where(
            RefreshTokenModel.user_id == user_id,
            RefreshTokenModel.device_id == device_id,
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def delete_all_by_user(self, user_id: UUID) -> None:
        stmt = sa.delete(RefreshTokenModel).where(RefreshTokenModel.user_id == user_id)
        await self.db.execute(stmt)
        await self.db.commit()
