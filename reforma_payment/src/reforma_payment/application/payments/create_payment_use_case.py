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
        payment = await self.payment_repo.create(
            user_id=request.user_id,
            provider_id=provider.id,
            amount=request.amount,
            currency=request.currency,
            idempotency_key=request.idempotency_key,
            description=request.description,
            payment_metadata=request.payment_metadata,
        )
        if request.provider_type == "stripe":
            client = StripeClient(
                secret_key=provider.credentials["secret_key"],
                webhook_secret=provider.credentials["webhook_secret"],
            )
            intent = client.create_payment_intent(
                amount=request.amount,
                currency=request.currency,
                idempotency_key=request.idempotency_key,
            )
            payment.redirect_url = intent.get("redirect_url")
            payment.client_secret = intent.get("client_secret")
        # another payment provider
        #     
        await self.payment_repo.update(payment)
        return payment
