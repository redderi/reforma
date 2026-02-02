import json
import aio_pika
from reforma_authorization.infrastructure.config.rabbitmq_config import (
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_USER,
    RABBITMQ_PASSWORD
)

RABBITMQ_URL = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/"

class RabbitMQConnection:
    def __init__(self):
        self.connection: aio_pika.RobustConnection | None = None
        self.channel: aio_pika.abc.AbstractChannel | None = None

    async def connect(self):
        self.connection = await aio_pika.connect_robust(RABBITMQ_URL, heartbeat=600)
        self.channel = await self.connection.channel()
        # Чтобы сообщения были persistent
        await self.channel.set_qos(prefetch_count=10)

    async def declare_exchange(self, exchange: str):
        if self.channel is None:
            raise RuntimeError("Channel not initialized. Call connect() first.")
        await self.channel.declare_exchange(
            name=exchange,
            type=aio_pika.ExchangeType.DIRECT,
            durable=True
        )

    async def publish(self, exchange: str, routing_key: str, message: dict):
        if self.channel is None:
            raise RuntimeError("Channel not initialized. Call connect() first.")

        await self.declare_exchange(exchange)

        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=routing_key
        )

    async def close(self):
        if self.connection:
            await self.connection.close()
