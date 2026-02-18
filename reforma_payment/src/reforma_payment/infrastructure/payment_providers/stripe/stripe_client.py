import stripe


class StripeClient:

    def __init__(self, secret_key: str, webhook_secret: str):
        stripe.api_key = secret_key
        self.webhook_secret = webhook_secret

    def create_payment_intent(self, amount: int, currency: str, idempotency_key: str):
        return stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            automatic_payment_methods={"enabled": True},
            idempotency_key=idempotency_key
        )

    def construct_event(self, payload, signature):
        return stripe.Webhook.construct_event(
            payload,
            signature,
            self.webhook_secret
        )
