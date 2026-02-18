from uuid import UUID
from reforma_payment.domain.repositories.payment_provider_repository import PaymentProviderRepository
from reforma_payment.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class DeletePaymentProviderUseCase:
    def __init__(self, repository: PaymentProviderRepository):
        self.repository = repository

    async def execute(self, provider_id: UUID) -> None:
        log_info(f"Начало удаления провайдера: {provider_id}", service="payment-service")
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    await self.repository.delete(provider_id)
                    log_info(f"Провайдер успешно удален: {provider_id}", service="payment-service")
                except Exception as e:
                    log_error(f"Ошибка при удалении провайдера {provider_id}: {e}", service="payment-service")
                    raise
