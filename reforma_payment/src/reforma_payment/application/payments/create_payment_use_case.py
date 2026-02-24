from reforma_payment.domain.repositories.payment_repository import PaymentRepository
from reforma_payment.domain.repositories.payment_provider_repository import (
    PaymentProviderRepository,
)
from reforma_payment.presentation.schemas.create_payment_request_schema import (
    CreatePaymentRequest,
)
from reforma_payment.infrastructure.payment_providers.stripe.stripe_client import (
    StripeClient,
)


class CreatePaymentUseCase:
    def __init__(
        self, payment_repo: PaymentRepository, provider_repo: PaymentProviderRepository
    ):
        self.payment_repo = payment_repo
        self.provider_repo = provider_repo

    async def execute(self, request: CreatePaymentRequest):
        provider = await self.provider_repo.get_active_by_type(request.provider_type)
        if not provider:
            raise ValueError(f"No active provider for type {request.provider_type}")

        # 1. Создаём запись в базе (ещё без Stripe-данных)
        payment = await self.payment_repo.create(
            user_id=request.user_id,
            provider_id=provider.id,
            amount=request.amount,
            currency=request.currency,
            idempotency_key=request.idempotency_key,
            description=request.description,
            payment_metadata=request.payment_metadata or {},
        )

        if request.provider_type == "stripe":
            client = StripeClient(
                secret_key=provider.credentials["secret_key"],
                webhook_secret=provider.credentials.get("webhook_secret"),
            )

            # Можно добавить return_url из фронта или сгенерировать
            # например: return_url = f"https://your-app.com/payment/success?payment_id={payment.id}"
            return_url = request.return_url  # ← добавь это поле в CreatePaymentRequest

            intent_data = client.create_payment_intent(
                amount=request.amount,
                currency=request.currency,
                idempotency_key=request.idempotency_key,
                metadata={
                    "payment_id": str(payment.id),
                    "user_id": str(request.user_id),
                },
                return_url=return_url,
            )

            # Обновляем запись в базе
            payment.provider_payment_id = intent_data["id"]
            payment.client_secret = intent_data["client_secret"]   # ← сохраняем для фронта
            payment.status = intent_data["status"]                 # initial → requires_payment_method / requires_confirmation

            await self.payment_repo.update(payment)

        return payment