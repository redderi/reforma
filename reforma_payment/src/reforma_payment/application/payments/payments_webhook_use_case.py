from typing import Any, Dict
from datetime import datetime
import stripe

from reforma_payment.domain.repositories.payment_repository import PaymentRepository
from reforma_payment.domain.repositories.payment_provider_repository import PaymentProviderRepository
from reforma_payment.infrastructure.payment_providers.stripe.stripe_client import StripeClient
from reforma_common.logger import log_info, log_warning, log_error
from reforma_payment.infrastructure.rabbitmq.publisher import EventPublisher
from reforma_payment.infrastructure.config.rabbitmq_config import (
    ADD_BALANCE_ROUTING_KEY,
    USER_EXCHANGE,
)


class PaymentWebhookUseCase:
    def __init__(
        self,
        payment_repo: PaymentRepository,
        provider_repo: PaymentProviderRepository,
        event_publisher: EventPublisher,
    ):
        self.payment_repo = payment_repo
        self.provider_repo = provider_repo
        self.event_publisher = event_publisher

    async def execute(
        self,
        payload: bytes,
        signature: str,
        provider_type: str,
    ) -> Dict[str, str]:
        """
        Обрабатывает входящий webhook от платёжного провайдера.
        На данный момент поддерживается только Stripe.
        """
        if provider_type != "stripe":
            log_warning(
                f"Unsupported webhook provider: {provider_type}",
                extra={"provider_type": provider_type}
            )
            raise ValueError(f"Unsupported provider type: {provider_type}")

        # Получаем активного провайдера
        provider = await self.provider_repo.get_active_by_type("stripe")
        if not provider:
            log_error("No active Stripe provider found")
            raise ValueError("No active Stripe provider configured")

        # Создаём клиент с нужными ключами
        client = StripeClient(
            secret_key=provider.credentials["secret_key"],
            webhook_secret=provider.credentials.get("webhook_secret"),
        )

        # Проверяем подпись и получаем событие
        try:
            event: stripe.Event = client.construct_event(payload, signature)
        except stripe.error.SignatureVerificationError as e:
            log_error(f"Webhook signature verification failed: {e}")
            raise ValueError(f"Invalid webhook signature: {str(e)}")
        except ValueError as e:
            log_error(f"Invalid webhook payload: {e}")
            raise ValueError(f"Invalid payload: {str(e)}")

        event_type = event.type
        data_object = event.data.object

        log_info(
            f"Processing Stripe webhook event: {event_type}",
            extra={
                "event_id": event.id,
                "event_type": event_type,
                "object_id": data_object.get("id"),
            }
        )

        # ──────────────────────────────────────────────────────
        # Основные события, которые стоит обрабатывать
        # ──────────────────────────────────────────────────────

        if event_type == "payment_intent.succeeded":
            await self._handle_payment_intent_succeeded(data_object)

        elif event_type == "payment_intent.payment_failed":
            await self._handle_payment_intent_failed(data_object)

        elif event_type == "checkout.session.completed":
            await self._handle_checkout_session_completed(data_object)

        elif event_type == "checkout.session.expired":
            log_info("Checkout session expired", extra={"session_id": data_object.id})

        elif event_type == "invoice.payment_succeeded":
            # для подписок — если в будущем понадобится
            log_info("Invoice payment succeeded", extra={"invoice_id": data_object.id})

        else:
            # необрабатываемые события просто логируем
            log_info(
                f"Unhandled Stripe event type: {event_type}",
                extra={"event_id": event.id}
            )

        return {"status": "ok"}

    async def _handle_payment_intent_succeeded(self, intent: stripe.PaymentIntent) -> None:
        """Обработка успешного Payment Intent"""
        payment_id = intent.metadata.get("payment_id")
        if not payment_id:
            log_warning("PaymentIntent succeeded without payment_id in metadata")
            return

        payment = await self.payment_repo.get_by_id(payment_id)
        if not payment:
            log_warning(f"Payment not found for external_id: {intent.id}")
            return

        if payment.status == "succeeded":
            log_info("Payment already succeeded, skipping duplicate event")
            return

        payment.status = "succeeded"
        payment.updated_at = datetime.utcnow()
        payment.provider_payment_data = intent.to_dict()  # если нужно сохранить весь объект

        await self.payment_repo.update(payment)

        # Отправляем событие на пополнение баланса
        await self.event_publisher.publish_event(
            exchange_name=USER_EXCHANGE,
            routing_key=ADD_BALANCE_ROUTING_KEY,
            payload={
                "user_id": str(payment.user_id),
                "amount": payment.amount,
                "currency": payment.currency,
                "payment_id": str(payment.id),
                "external_id": intent.id,
                "metadata": payment.payment_metadata or {},
                "event_type": "payment.succeeded",
            },
        )

        log_info(
            "Payment succeeded and balance event published",
            extra={"payment_id": payment.id, "external_id": intent.id}
        )

    async def _handle_payment_intent_failed(self, intent: stripe.PaymentIntent) -> None:
        """Обработка провала платежа"""
        payment_id = intent.metadata.get("payment_id")
        if not payment_id:
            return

        payment = await self.payment_repo.get_by_id(payment_id)
        if not payment:
            return

        payment.status = "failed"
        payment.updated_at = datetime.utcnow()
        payment.error_message = intent.last_payment_error.message if intent.last_payment_error else None

        await self.payment_repo.update(payment)

        log_warning(
            "Payment failed",
            extra={
                "payment_id": payment.id,
                "external_id": intent.id,
                "error": payment.error_message,
            }
        )

    async def _handle_checkout_session_completed(self, session: stripe.checkout.Session) -> None:
        """Обработка завершения Checkout сессии (если используете hosted Checkout)"""
        payment_id = session.metadata.get("payment_id")
        if not payment_id:
            log_warning("Checkout session completed without payment_id")
            return

        payment = await self.payment_repo.get_by_id(payment_id)
        if not payment:
            return

        if session.payment_status == "paid":
            payment.status = "succeeded"
            payment.updated_at = datetime.utcnow()
            await self.payment_repo.update(payment)

            # Публикуем событие пополнения
            await self.event_publisher.publish_event(
                exchange_name=USER_EXCHANGE,
                routing_key=ADD_BALANCE_ROUTING_KEY,
                payload={
                    "user_id": str(payment.user_id),
                    "amount": payment.amount,
                    "currency": payment.currency,
                    "payment_id": str(payment.id),
                    "external_id": session.id,
                },
            )

            log_info("Checkout session completed → payment succeeded")
        else:
            log_warning(f"Checkout session completed with status: {session.payment_status}")