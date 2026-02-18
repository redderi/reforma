from reforma_payment.domain.entities.payment_provider import PaymentProvider
from reforma_payment.domain.repositories.payment_provider_repository import PaymentProviderRepository
from reforma_payment.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_warning, log_error


class GetActiveProviderByTypeUseCase:
    def __init__(self, repository: PaymentProviderRepository):
        self.repository = repository

    async def execute(self, provider_type: str) -> PaymentProvider | None:
        log_info(f"Начало поиска активного провайдера по типу: {provider_type}", service="payment-service")
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    provider = await self.repository.get_active_by_type(provider_type)
                    if provider:
                        log_info(f"Найден активный провайдер: {provider.id}", service="payment-service")
                    else:
                        log_warning(f"Активный провайдер типа {provider_type} не найден", service="payment-service")
                    return provider
                except Exception as e:
                    log_error(f"Ошибка при поиске активного провайдера типа {provider_type}: {e}", service="payment-service")
                    raise
