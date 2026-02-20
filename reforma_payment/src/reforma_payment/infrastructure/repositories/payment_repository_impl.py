from typing import List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from reforma_payment.domain.entities.payment import Payment
from reforma_payment.domain.repositories.payment_repository import PaymentRepository
from reforma_payment.infrastructure.db.models import PaymentModel


class PaymentRepositoryImpl(PaymentRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        result = await self.db.execute(
            select(PaymentModel).where(PaymentModel.id == payment_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def get_by_external_id(self, external_id: str) -> Payment | None:
        result = await self.db.execute(
            select(PaymentModel).where(PaymentModel.external_id == external_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def find_by_idempotency(self, idempotency_key: str) -> Payment | None:
        result = await self.db.execute(
            select(PaymentModel).where(PaymentModel.idempotency_key == idempotency_key)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def get_by_user(
        self, user_id: UUID, limit: int = 20, offset: int = 0
    ) -> List[Payment]:
        result = await self.db.execute(
            select(PaymentModel)
            .where(PaymentModel.user_id == user_id)
            .order_by(PaymentModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_pending_by_user(self, user_id: UUID) -> List[Payment]:
        result = await self.db.execute(
            select(PaymentModel)
            .where(PaymentModel.user_id == user_id)
            .where(PaymentModel.status.in_(["pending", "processing"]))
            .order_by(PaymentModel.created_at.desc())
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def create(self, payment: Payment) -> Payment:
        model = PaymentModel(
            id=payment.id,
            user_id=payment.user_id,
            provider_id=payment.provider_id,
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
            payment_metadata=payment.payment_metadata,
            idempotency_key=payment.idempotency_key,
            external_id=payment.external_id,
            client_secret=payment.client_secret,
        )
        self.db.add(model)
        await self.db.flush()
        return self._to_entity(model)

    async def update_status(
        self,
        payment_id: UUID,
        new_status: str,
        external_id: str | None = None,
        redirect_url: str | None = None,
        client_secret: str | None = None,
        updated_at: datetime | None = None,
    ) -> Payment:
        stmt = (
            update(PaymentModel)
            .where(PaymentModel.id == payment_id)
            .values(
                status=new_status,
                external_id=external_id,
                redirect_url=redirect_url,
                client_secret=client_secret,
                updated_at=updated_at or datetime.utcnow(),
            )
            .returning(PaymentModel)
        )
        result = await self.db.execute(stmt)
        model = result.scalar_one()
        if not model:
            raise ValueError(f"Платёж {payment_id} не найден")
        await self.db.flush()
        return self._to_entity(model)

    async def mark_as_succeeded(
        self, payment_id: UUID, external_id: str, completed_at: datetime
    ) -> Payment:
        return await self.update_status(
            payment_id=payment_id,
            new_status="succeeded",
            external_id=external_id,
            completed_at=completed_at,
        )

    async def mark_as_failed(
        self,
        payment_id: UUID,
        error_message: str | None = None,
        completed_at: datetime | None = None,
    ) -> Payment:
        return await self.update_status(
            payment_id=payment_id,
            new_status="failed",
            error_message=error_message,
            completed_at=completed_at or datetime.utcnow(),
        )

    async def exists(self, payment_id: UUID) -> bool:
        result = await self.db.execute(
            select(1)
            .select_from(PaymentModel)
            .where(PaymentModel.id == payment_id)
            .limit(1)
        )
        return result.scalar() is not None

    async def count_by_user(self, user_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(PaymentModel)
            .where(PaymentModel.user_id == user_id)
        )
        return result.scalar() or 0

    async def count_pending_by_user(self, user_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(PaymentModel)
            .where(PaymentModel.user_id == user_id)
            .where(PaymentModel.status.in_(["pending", "processing"]))
        )
        return result.scalar() or 0

    def _to_entity(self, model: PaymentModel) -> Payment:
        return Payment(
            id=model.id,
            user_id=model.user_id,
            provider_id=model.provider_id,
            amount=model.amount,
            currency=model.currency,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
            payment_metadata=model.payment_metadata,
            idempotency_key=model.idempotency_key,
            external_id=model.external_id,
            client_secret=model.client_secret,
        )
