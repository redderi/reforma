from uuid import UUID
from reforma_payment.domain.entities.payment_provider import PaymentProvider
from reforma_payment.src.reforma_payment.domain.repositories.payment_provider_repository import PaymentProviderRepository
from reforma_payment.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_warning, log_error


class GetPaymentProviderByIdUseCase:
    def __init__(self, repository: PaymentProviderRepository):
        self.repository = repository

    async def execute(self, provider_id: UUID) -> PaymentProvider | None:
        log_info(f"Начало получения провайдера платежей по ID: {provider_id}", service="payment-service")
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    provider = await self.repository.get_by_id(provider_id)
                    if provider:
                        log_info(f"Провайдер платежей успешно получен: {provider_id}", service="payment-service")
                    else:
                        log_warning(f"Провайдер платежей не найден: {provider_id}", service="payment-service")
                    return provider
                except Exception as e:
                    log_error(f"Ошибка при получении провайдера {provider_id}: {e}", service="payment-service")
                    raise
