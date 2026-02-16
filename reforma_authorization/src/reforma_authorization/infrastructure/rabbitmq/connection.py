import json
import aio_pika
from typing import Optional
from reforma_authorization.infrastructure.config.rabbitmq_config import (
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_USER,
    RABBITMQ_PASSWORD,
)
from reforma_common.logger import log_info, log_error

RABBITMQ_URL = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/"


class RabbitMQConnection:
    def __init__(self):
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.RobustChannel] = None

    async def connect(self):
        if self.connection and not self.connection.is_closed:
            return

        try:
            self.connection = await aio_pika.connect_robust(
                RABBITMQ_URL,
                heartbeat=30,
                timeout=10
            )
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)

            log_info("RabbitMQ connected", service="auth-service")

        except Exception as e:
            log_error(f"RabbitMQ connection error: {e}", service="auth-service")
            raise

    async def get_exchange(self, exchange_name: str) -> aio_pika.Exchange:
        if not self.channel:
            raise RuntimeError("RabbitMQ channel is not initialized")

        return await self.channel.declare_exchange(
            name=exchange_name,
            type=aio_pika.ExchangeType.DIRECT,
            durable=True,
        )

    async def declare_queue(self, queue_name: str) -> aio_pika.Queue:
        if not self.channel:
            raise RuntimeError("RabbitMQ channel is not initialized")

        return await self.channel.declare_queue(
            name=queue_name,
            durable=True,
        )

    async def bind_queue(self, exchange_name: str, queue_name: str, routing_key: str):
        exchange = await self.get_exchange(exchange_name)
        queue = await self.declare_queue(queue_name)
        await queue.bind(exchange, routing_key=routing_key)

    async def publish(self, exchange_name: str, routing_key: str, message: dict):
        if not self.channel:
            await self.connect()

        exchange = await self.get_exchange(exchange_name)

        body = json.dumps(message).encode()

        await exchange.publish(
            aio_pika.Message(
                body=body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_type="application/json",
            ),
            routing_key=routing_key,
        )

        log_info(
            "RabbitMQ message published",
            service="auth-service",
            context={
                "exchange": exchange_name,
                "routing_key": routing_key,
                "message": message,
            },
        )

    async def close(self):
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            log_info("RabbitMQ connection closed", service="auth-service")
