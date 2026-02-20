import json
import aio_pika
from reforma_mail.infrastructure.rabbitmq.connection import RabbitMQConnection
from reforma_mail.application.handlers.email_verification_handler import (
    EmailVerificationHandler,
)
from reforma_mail.application.handlers.password_change_handler import (
    PasswordChangeHandler,
)
from reforma_mail.infrastructure.config.rabbitmq_config import (
    MAIL_EXCHANGE,
    MAIL_QUEUE,
    EMAIL_VERIFICATION_ROUTING_KEY,
    CHANGE_PASSWORD_ROUTING_KEY,
    USER_RESTORE_ROUTING_KEY,
)
from reforma_mail.application.handlers.user_restore_handler import UserRestoreHandler
from reforma_common.logger import log_info, log_error, log_warning
HANDLERS = {
    EMAIL_VERIFICATION_ROUTING_KEY: EmailVerificationHandler(),
    CHANGE_PASSWORD_ROUTING_KEY: PasswordChangeHandler(),
    USER_RESTORE_ROUTING_KEY: UserRestoreHandler(),
}


class MailConsumer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.rabbit = RabbitMQConnection()
            cls._instance._connected = False
        return cls._instance

    async def connect(self):
        if not self._connected:
            try:
                await self.rabbit.connect()
                self._connected = True

                log_info(
                    "RabbitMQ connection established for mail consumer",
                    service="mail-service",
                    context={"exchange": MAIL_EXCHANGE, "queue": MAIL_QUEUE},
                )
            except Exception as e:
                log_error(
                    "Failed to establish RabbitMQ connection for mail consumer",
                    service="mail-service",
                    context={
                        "exchange": MAIL_EXCHANGE,
                        "queue": MAIL_QUEUE,
                        "error_detail": str(e),
                    },
                )
                raise

    async def start_consuming(self):
        if not self._connected:
            await self.connect()

        try:
            channel = self.rabbit.channel
            exchange = await channel.declare_exchange(
                MAIL_EXCHANGE, aio_pika.ExchangeType.DIRECT, durable=True
            )
            queue = await channel.declare_queue(MAIL_QUEUE, durable=True)
            await queue.bind(exchange, routing_key=EMAIL_VERIFICATION_ROUTING_KEY)
            await queue.bind(exchange, routing_key=CHANGE_PASSWORD_ROUTING_KEY)
            await queue.bind(exchange, routing_key=USER_RESTORE_ROUTING_KEY)
            log_info(
                "Mail consumer started consuming",
                service="mail-service",
                context={
                    "exchange": MAIL_EXCHANGE,
                    "queue": MAIL_QUEUE,
                    "routing_keys": [
                        EMAIL_VERIFICATION_ROUTING_KEY,
                        CHANGE_PASSWORD_ROUTING_KEY,
                        USER_RESTORE_ROUTING_KEY,
                    ],
                },
            )
            async def callback(message: aio_pika.IncomingMessage):
                async with message.process():
                    try:
                        data = json.loads(message.body.decode())
                        event_type = data.get("type")
                        payload = data.get("payload")

                        handler = HANDLERS.get(event_type)
                        if handler:
                            await handler.handle(payload)
                            log_info(
                                "Event processed successfully",
                                service="mail-service",
                                context={
                                    "event_type": event_type,
                                    "routing_key": message.routing_key,
                                },
                            )
                        else:
                            log_warning(
                                "Unknown event type received",
                                service="mail-service",
                                context={
                                    "event_type": event_type,
                                    "routing_key": message.routing_key,
                                },
                            )

                    except Exception as e:
                        log_error(
                            "Error processing incoming message",
                            service="mail-service",
                            context={
                                "routing_key": message.routing_key,
                                "error_detail": str(e),
                            },
                        )
                        # await message.nack(requeue=True)

            await queue.consume(callback)

        except Exception as e:
            log_error(
                "Failed to start mail consumer",
                service="mail-service",
                context={
                    "exchange": MAIL_EXCHANGE,
                    "queue": MAIL_QUEUE,
                    "error_detail": str(e),
                },
            )
            raise

    async def close(self):
        if self._connected:
            try:
                await self.rabbit.close()
                self._connected = False

                log_info(
                    "RabbitMQ connection closed for mail consumer",
                    service="mail-service",
                )
            except Exception as e:
                log_error(
                    "Error while closing RabbitMQ connection for mail consumer",
                    service="mail-service",
                    context={"error_detail": str(e)},
                )
