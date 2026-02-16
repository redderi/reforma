from datetime import datetime, timedelta
import secrets
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from reforma_authorization.domain.repositories.email_verification_token_repository import EmailVerificationTokenRepository
from reforma_authorization.domain.entities.email_verification_token import EmailVerificationToken
from reforma_authorization.infrastructure.db.models import EmailVerificationTokenModel


class EmailTokenRepositoryImpl(EmailVerificationTokenRepository):

    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_entity(self, model: EmailVerificationTokenModel) -> EmailVerificationToken:
        return EmailVerificationToken(
            user_id=model.user_id,
            token=model.token,
            expires_at=model.expires_at,
            data=model.data
        )

    async def save(self, token: EmailVerificationToken) -> EmailVerificationToken:
        model = EmailVerificationTokenModel(
            user_id=token.user_id,
            token=token.token,
            expires_at=token.expires_at,
            data=token.data
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return self._to_entity(model)

    async def delete(self, token_str: str) -> None:
        result = await self.db.execute(
            select(EmailVerificationTokenModel).filter_by(token=token_str)
        )
        model = result.scalar_one_or_none()
        if model:
            await self.db.delete(model)
            await self.db.commit()

    async def get(self, token_str: str) -> EmailVerificationToken | None:
        result = await self.db.execute(
            select(EmailVerificationTokenModel).filter_by(token=token_str)
        )
        model = result.scalar_one_or_none()
        if not model or model.expires_at < datetime.utcnow():
            return None
        return self._to_entity(model)

    async def create_token(
        self, 
        user_id: UUID, 
        hours_valid: int = 24, 
        data: dict | None = None
    ) -> EmailVerificationToken:
        token_str = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=hours_valid)
        token = EmailVerificationToken(
            user_id=user_id,
            token=token_str,
            expires_at=expires_at,
            data=data or {}
        )
        return await self.save(token)

