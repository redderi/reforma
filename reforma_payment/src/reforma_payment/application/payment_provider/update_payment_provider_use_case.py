from reforma_payment.domain.entities.payment_provider import PaymentProvider
from reforma_payment.domain.repositories.payment_provider_repository import PaymentProviderRepository
from reforma_payment.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class UpdatePaymentProviderUseCase:
    def __init__(self, repository: PaymentProviderRepository):
        self.repository = repository

    async def execute(self, provider: PaymentProvider) -> PaymentProvider:
        log_info(f"Начало обновления провайдера платежей: {provider.id}", service="payment-service")
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated_provider = await self.repository.update(provider)
                    log_info(f"Провайдер платежей успешно обновлен: {updated_provider.id}", service="payment-service")
                    return updated_provider
                except Exception as e:
                    log_error(f"Ошибка при обновлении провайдера {provider.id}: {e}", service="payment-service")
                    raise
