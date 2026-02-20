from reforma_payment.domain.entities.payment_provider import PaymentProvider
from reforma_payment.domain.repositories.payment_provider_repository import (
    PaymentProviderRepository,
)
from reforma_payment.infrastructure.db.session import SessionLocal


class AddPaymentProviderUseCase:
    def __init__(self, repository: PaymentProviderRepository):
        self.repository = repository

    async def execute(self, provider: PaymentProvider) -> PaymentProvider:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    new_provider = await self.repository.add(provider)
                    return new_provider
                except Exception:
                    raise
