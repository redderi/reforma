# reforma_payment/application/payments/create_payment_use_case.py
from reforma_payment.domain.repositories.payment_repository import PaymentRepository
from reforma_payment.domain.repositories.payment_provider_repository import PaymentProviderRepository
from reforma_payment.presentation.schemas.create_payment_request_schema import CreatePaymentRequest
from reforma_common.logger import log_info, log_error
from reforma_payment.infrastructure.payment_providers.stripe.stripe_client import StripeClient
# Можно добавить YooKassaClient и других провайдеров

class CreatePaymentUseCase:
    def __init__(self, payment_repo: PaymentRepository, provider_repo: PaymentProviderRepository):
        self.payment_repo = payment_repo
        self.provider_repo = provider_repo

    async def execute(self, request: CreatePaymentRequest):
        # Берем активного провайдера по типу
        provider = await self.provider_repo.get_active_by_type(request.provider_type)
        if not provider:
            log_error(f"No active provider for type {request.provider_type}", service="payment-service")
            raise ValueError(f"No active provider for type {request.provider_type}")

        # Создаем платеж в базе
        payment = await self.payment_repo.create_payment(
            user_id=request.user_id,
            provider_id=provider.id,
            amount=request.amount,
            currency=request.currency,
            idempotency_key=request.idempotency_key,
            description=request.description,
            metadata=request.metadata
        )

        # Генерируем redirect/client_secret для конкретного провайдера
        if request.provider_type == "stripe":
            client = StripeClient(
                secret_key=provider.credentials["secret_key"],
                webhook_secret=provider.credentials["webhook_secret"]
            )
            intent = client.create_payment_intent(
                amount=request.amount,
                currency=request.currency,
                idempotency_key=request.idempotency_key
            )
            payment.redirect_url = intent.get("redirect_url")
            payment.client_secret = intent.get("client_secret")
        # elif request.provider_type == "yookassa":
        #     ... аналогично для YooKassa

        # Обновляем платеж с данными провайдера
        await self.payment_repo.update(payment)
        log_info(f"Payment {payment.id} created via {request.provider_type}", service="payment-service")
        return payment
