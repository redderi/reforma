from reforma_payment.domain.entities.payment_provider import PaymentProvider
from reforma_payment.domain.repositories.payment_provider_repository import (
    PaymentProviderRepository,
)
from reforma_payment.infrastructure.db.session import SessionLocal


class UpdatePaymentProviderUseCase:
    def __init__(self, repository: PaymentProviderRepository):
        self.repository = repository

    async def execute(self, provider: PaymentProvider) -> PaymentProvider:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated_provider = await self.repository.update(provider)
                    return updated_provider
                except Exception:
                    raise
