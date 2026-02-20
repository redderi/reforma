import json
import aio_pika
from typing import Optional
from reforma_mail.infrastructure.config.rabbitmq_config import (
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_USER,
    RABBITMQ_PASSWORD,
)
from reforma_common.logger import log_info, log_error

RABBITMQ_URL = (
    f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/"
)


class RabbitMQConnection:
    def __init__(self):
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.RobustChannel] = None

    async def connect(self):
        if self.connection and not self.connection.is_closed:
            return

        try:
            self.connection = await aio_pika.connect_robust(
                RABBITMQ_URL, heartbeat=30, timeout=10
            )
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)

            log_info(
                "RabbitMQ connection established",
                service="auth-service",
                context={"host": RABBITMQ_HOST, "port": RABBITMQ_PORT, "heartbeat": 30},
            )

        except Exception as e:
            log_error(
                "Failed to establish RabbitMQ connection",
                service="auth-service",
                context={
                    "host": RABBITMQ_HOST,
                    "port": RABBITMQ_PORT,
                    "error_detail": str(e),
                },
            )
            raise

    async def get_exchange(self, exchange_name: str) -> aio_pika.Exchange:
        if not self.channel:
            raise RuntimeError("RabbitMQ channel is not initialized")

        try:
            exchange = await self.channel.declare_exchange(
                name=exchange_name,
                type=aio_pika.ExchangeType.DIRECT,
                durable=True,
            )
            log_info(
                "Exchange declared or retrieved",
                service="auth-service",
                context={"exchange_name": exchange_name},
            )
            return exchange
        except Exception as e:
            log_error(
                "Failed to declare or retrieve exchange",
                service="auth-service",
                context={"exchange_name": exchange_name, "error_detail": str(e)},
            )
            raise

    async def declare_queue(self, queue_name: str) -> aio_pika.Queue:
        if not self.channel:
            raise RuntimeError("RabbitMQ channel is not initialized")

        try:
            queue = await self.channel.declare_queue(
                name=queue_name,
                durable=True,
            )
            log_info(
                "Queue declared or retrieved",
                service="auth-service",
                context={"queue_name": queue_name},
            )
            return queue
        except Exception as e:
            log_error(
                "Failed to declare or retrieve queue",
                service="auth-service",
                context={"queue_name": queue_name, "error_detail": str(e)},
            )
            raise

    async def bind_queue(self, exchange_name: str, queue_name: str, routing_key: str):
        try:
            exchange = await self.get_exchange(exchange_name)
            queue = await self.declare_queue(queue_name)
            await queue.bind(exchange, routing_key=routing_key)

            log_info(
                "Queue bound to exchange",
                service="auth-service",
                context={
                    "exchange_name": exchange_name,
                    "queue_name": queue_name,
                    "routing_key": routing_key,
                },
            )
        except Exception as e:
            log_error(
                "Failed to bind queue to exchange",
                service="auth-service",
                context={
                    "exchange_name": exchange_name,
                    "queue_name": queue_name,
                    "routing_key": routing_key,
                    "error_detail": str(e),
                },
            )
            raise

    async def publish(self, exchange_name: str, routing_key: str, message: dict):
        if not self.channel:
            await self.connect()

        try:
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
                "RabbitMQ message published successfully",
                service="auth-service",
                context={
                    "exchange": exchange_name,
                    "routing_key": routing_key,
                    "message_size_bytes": len(body),
                    "message_type": message.get("type", "unknown"),
                },
            )

        except Exception as e:
            log_error(
                "Failed to publish message to RabbitMQ",
                service="auth-service",
                context={
                    "exchange": exchange_name,
                    "routing_key": routing_key,
                    "message_size_bytes": len(json.dumps(message).encode())
                    if message
                    else 0,
                    "error_detail": str(e),
                },
            )
            raise

    async def close(self):
        if self.connection and not self.connection.is_closed:
            try:
                await self.connection.close()
                log_info(
                    "RabbitMQ connection closed successfully", service="auth-service"
                )
            except Exception as e:
                log_error(
                    "Error while closing RabbitMQ connection",
                    service="auth-service",
                    context={"error_detail": str(e)},
                )
