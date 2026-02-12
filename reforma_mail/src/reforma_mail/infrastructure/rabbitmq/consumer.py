import json
import aio_pika
from reforma_mail.infrastructure.rabbitmq.connection import RabbitMQConnection
from reforma_mail.application.handlers.email_verification_handler import EmailVerificationHandler
from reforma_mail.application.handlers.password_reset_handler import PasswordResetHandler
from reforma_mail.infrastructure.config.rabbitmq_config import MAIL_EXCHANGE, MAIL_QUEUE, EMAIL_VERIFICATION_ROUTING_KEY
from reforma_mail.common.logger import log_info, log_error

HANDLERS = {
    EMAIL_VERIFICATION_ROUTING_KEY: EmailVerificationHandler(),
    "PASSWORD_RESET": PasswordResetHandler(),
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
            await self.rabbit.connect()
            self._connected = True

    async def start_consuming(self):
        if not self._connected:
            await self.connect()

        channel = self.rabbit.channel

        # Декларируем exchange
        exchange = await channel.declare_exchange(
            MAIL_EXCHANGE,
            aio_pika.ExchangeType.DIRECT,
            durable=True
        )

        # Декларируем очередь
        queue = await channel.declare_queue(MAIL_QUEUE, durable=True)

        # Привязываем ключи маршрутизации
        await queue.bind(exchange, routing_key=EMAIL_VERIFICATION_ROUTING_KEY)
        await queue.bind(exchange, routing_key="PASSWORD_RESET")
        log_info("Start Consuming", service="mail_service")

        async def callback(message: aio_pika.IncomingMessage):
            async with message.process():
                data = json.loads(message.body.decode())
                event_type = data.get("type")
                payload = data.get("payload")

                handler = HANDLERS.get(event_type)
                if handler:
                    handler.handle(payload)
                else:
                    print(f"[MailConsumer] Unknown event type: {event_type}")

        # Запускаем потребление
        await queue.consume(callback)

    async def close(self):
        if self._connected:
            await self.rabbit.close()
            self._connected = False
