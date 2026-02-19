from reforma_payment.infrastructure.rabbitmq.connection import RabbitMQConnection
from reforma_common.logger import log_info, log_error

class EventPublisher:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventPublisher, cls).__new__(cls)
            cls._instance.rabbit = RabbitMQConnection()
            cls._instance._connected = False
        return cls._instance

    async def connect(self):
        if not self._connected:
            await self.rabbit.connect()
            self._connected = True

    async def publish_event(
        self,
        exchange_name: str,
        event_type: str,
        payload: dict,
        routing_key: str | None = None
    ):
        if not self._connected:
            await self.connect()
        try:
            routing = routing_key or event_type
            message = {
                "type": event_type,
                "payload": payload
            }
            log_info(f"[Publisher] Sending event to {exchange_name} rk={routing}", service="payment-service")
            await self.rabbit.publish(exchange_name, routing, message)
            log_info("[Publisher] Event sent successfully", service="payment-service")
        except Exception as e:
            log_error(f"[Publisher] Event publish failed: {e}")

    async def close(self):
        if self._connected:
            await self.rabbit.close()
            self._connected = False
