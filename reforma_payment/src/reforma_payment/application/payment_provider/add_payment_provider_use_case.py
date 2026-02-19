from reforma_payment.domain.entities.payment_provider import PaymentProvider
from reforma_payment.domain.repositories.payment_provider_repository import PaymentProviderRepository
from reforma_payment.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error

class AddPaymentProviderUseCase:
    def __init__(self, repository: PaymentProviderRepository):
        self.repository = repository

    async def execute(self, provider: PaymentProvider) -> PaymentProvider:
        log_info(f"Начало добавления провайдера платежей: {provider.name}", service="payment-service")
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    new_provider = await self.repository.add(provider)
                    log_info(f"Провайдер платежей успешно добавлен: {new_provider.id}", service="payment-service")
                    return new_provider
                except Exception as e:
                    log_error(f"Ошибка при добавлении провайдера {provider.name}: {e}", service="payment-service")
                    raise
