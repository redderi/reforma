from uuid import UUID
from reforma_payment.domain.repositories.payment_provider_repository import (
    PaymentProviderRepository,
)
from reforma_payment.infrastructure.db.session import SessionLocal


class DeletePaymentProviderUseCase:
    def __init__(self, repository: PaymentProviderRepository):
        self.repository = repository

    async def execute(self, provider_id: UUID) -> None:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    await self.repository.delete(provider_id)
                except Exception:
                    raise
