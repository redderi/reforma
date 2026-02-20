from uuid import UUID
from reforma_payment.domain.entities.payment_provider import PaymentProvider
from reforma_payment.domain.repositories.payment_provider_repository import (
    PaymentProviderRepository,
)
from reforma_payment.infrastructure.db.session import SessionLocal


class GetPaymentProviderByIdUseCase:
    def __init__(self, repository: PaymentProviderRepository):
        self.repository = repository

    async def execute(self, provider_id: UUID) -> PaymentProvider | None:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    provider = await self.repository.get_by_id(provider_id)
                    return provider
                except Exception:
                    raise
