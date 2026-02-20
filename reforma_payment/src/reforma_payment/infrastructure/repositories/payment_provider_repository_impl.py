from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from reforma_payment.domain.entities.payment_provider import PaymentProvider
from reforma_payment.infrastructure.db.models import PaymentProviderModel


class PaymentProviderRepositoryImpl:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, provider: PaymentProvider) -> PaymentProvider:
        model = PaymentProviderModel(
            id=provider.id,
            name=provider.name,
            provider_type=provider.provider_type,
            credentials=provider.credentials,
            is_active=provider.is_active,
            created_at=provider.created_at,
        )
        self.session.add(model)
        await self.session.commit()
        return provider

    async def get_by_id(self, provider_id: UUID) -> PaymentProvider | None:
        result = await self.session.get(PaymentProviderModel, provider_id)
        if not result:
            return None
        return PaymentProvider(
            id=result.id,
            name=result.name,
            provider_type=result.provider_type,
            credentials=result.credentials,
            is_active=result.is_active,
            created_at=result.created_at,
        )

    async def get_active_by_type(self, provider_type: str) -> PaymentProvider | None:
        result = await self.session.execute(
            select(PaymentProviderModel).where(
                PaymentProviderModel.provider_type == provider_type,
                PaymentProviderModel.is_active,
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return PaymentProvider(
            id=row.id,
            name=row.name,
            provider_type=row.provider_type,
            credentials=row.credentials,
            is_active=row.is_active,
            created_at=row.created_at,
        )

    async def list_active(self) -> List[PaymentProvider]:
        result = await self.session.execute(
            select(PaymentProviderModel).where(PaymentProviderModel.is_active)
        )
        rows = result.scalars().all()
        return [
            PaymentProvider(
                id=row.id,
                name=row.name,
                provider_type=row.provider_type,
                credentials=row.credentials,
                is_active=row.is_active,
                created_at=row.created_at,
            )
            for row in rows
        ]

    async def update(self, provider: PaymentProvider) -> PaymentProvider:
        await self.session.execute(
            update(PaymentProviderModel)
            .where(PaymentProviderModel.id == provider.id)
            .values(
                name=provider.name,
                provider_type=provider.provider_type,
                credentials=provider.credentials,
                is_active=provider.is_active,
            )
        )
        await self.session.commit()
        return provider

    async def activate(self, provider_id: UUID) -> None:
        await self.session.execute(
            update(PaymentProviderModel)
            .where(PaymentProviderModel.id == provider_id)
            .values(is_active=True)
        )
        await self.session.commit()

    async def deactivate(self, provider_id: UUID) -> None:
        await self.session.execute(
            update(PaymentProviderModel)
            .where(PaymentProviderModel.id == provider_id)
            .values(is_active=False)
        )
        await self.session.commit()

    async def delete(self, provider_id: UUID) -> None:
        await self.session.execute(
            delete(PaymentProviderModel).where(PaymentProviderModel.id == provider_id)
        )
        await self.session.commit()
