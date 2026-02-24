import stripe


class StripeClient:
    def __init__(self, secret_key: str, webhook_secret: str | None = None):
        stripe.api_key = secret_key
        self.webhook_secret = webhook_secret

    def create_payment_intent(
        self,
        amount: int,
        currency: str,
        idempotency_key: str,
        metadata: dict | None = None,
        return_url: str | None = None,          # ← важно для 3DS-редиректа
    ) -> dict:
        params = {
            "amount": amount,
            "currency": currency.lower(),
            "automatic_payment_methods": {"enabled": True},
            "idempotency_key": idempotency_key,
            "metadata": metadata or {},
        }

        if return_url:
            params["payment_method_options"] = {
                "card": {"setup_future_usage": "off_session"}  # если нужно сохранять карту
            }

        intent = stripe.PaymentIntent.create(**params)

        return {
            "id": intent.id,
            "client_secret": intent.client_secret,          # ← вот это нужно фронту!
            "status": intent.status,
            # redirect_url не нужен для PaymentIntent + Elements
            # если используешь hosted Checkout — тогда да, но сейчас у тебя PaymentIntent
        }