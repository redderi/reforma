from reforma_payment.domain.repositories.payment_repository import PaymentRepository
from reforma_payment.domain.repositories.payment_provider_repository import PaymentProviderRepository
from reforma_payment.infrastructure.payment_providers.stripe.stripe_client import StripeClient
from reforma_common.logger import log_info, log_error
from datetime import datetime

from reforma_payment.infrastructure.rabbitmq.publisher import EventPublisher
from reforma_payment.infrastructure.config.rabbitmq_config import ADD_BALANCE_ROUTING_KEY, USER_EXCHANGE


class PaymentWebhookUseCase:
    def __init__(
        self, 
        payment_repo: PaymentRepository, 
        provider_repo: PaymentProviderRepository, 
        event_publisher: EventPublisher
    ):
        self.payment_repo = payment_repo
        self.provider_repo = provider_repo
        self.event_publisher = event_publisher

    async def execute(self, payload: bytes, signature: str, provider_type: str):
        # Берем активного провайдера нужного типа
        provider = await self.provider_repo.get_active_by_type(provider_type)
        if not provider:
            log_error(f"No active provider found for type '{provider_type}'", service="payment-service")
            raise ValueError(f"No active provider found for type '{provider_type}'")

        # Определяем клиента по провайдеру
        if provider_type == "stripe":
            client = StripeClient(
                secret_key=provider.credentials["secret_key"],
                webhook_secret=provider.credentials["webhook_secret"]
            )
        else:
            log_error(f"Unsupported provider type '{provider_type}'", service="payment-service")
            raise ValueError(f"Unsupported provider type '{provider_type}'")

        # Проверяем и строим событие
        try:
            event = client.construct_event(payload, signature)
        except ValueError as e:
            log_error(f"{provider_type} webhook signature verification failed: {e}", service="payment-service")
            raise ValueError("Invalid signature")

        # Обработка события успешного платежа
        if provider_type == "stripe" and event.type == "payment_intent.succeeded":
            intent = event.data.object
            payment = await self.payment_repo.get_by_external_id(intent.id)
            if payment:
                payment.status = "succeeded"
                payment.updated_at = datetime.utcnow()
                await self.payment_repo.update(payment)
                log_info(f"Payment {payment.id} marked as succeeded via {provider_type} webhook", service="payment-service")

                # --- Публикуем событие для начисления баллов в survey ---
                await self.event_publisher.publish_event(
                    exchange_name=USER_EXCHANGE,
                    event_type=ADD_BALANCE_ROUTING_KEY,
                    payload={
                        "user_id": str(payment.user_id),
                        "amount": payment.amount,
                        "currency": payment.currency,
                        "payment_id": str(payment.id),
                        "payment_metadata": payment.payment_metadata
                    }
                )
            else:
                log_error(f"No payment found for external_id {intent.id}", service="payment-service")

        return {"status": "ok"}
