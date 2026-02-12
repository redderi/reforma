import asyncio
import json
from reforma_authorization.infrastructure.rabbitmq.connection import RabbitMQConnection
from reforma_authorization.infrastructure.config.rabbitmq_config import MAIL_EXCHANGE
from reforma_authorization.common.logger import log_info, log_error
import aio_pika

class MailPublisher:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MailPublisher, cls).__new__(cls)
            cls._instance.rabbit = RabbitMQConnection()
            cls._instance._connected = False
        return cls._instance

    async def connect(self):
        if not self._connected:
            await self.rabbit.connect()
            self._connected = True

    async def send_event(self, event_type: str, payload: dict):

        message = {
            "type": event_type,
            "payload": payload
        }
        await self.publish(message, routing_key=event_type)

    async def publish(self, message: dict, routing_key: str):
        if not self._connected:
            await self.connect()
        try:
            log_info(f"[Publisher] Trying to send to {MAIL_EXCHANGE} rk={routing_key}")
            await self.rabbit.publish(MAIL_EXCHANGE, routing_key, message)
            log_info("[Publisher] Message sent successfully")
        except aio_pika.exceptions.ChannelLockedResource as e:
            log_error(f"[Publisher] Blocked by RabbitMQ alarm/resource limit: {e}")
        except Exception as e:
            log_error(f"[Publisher] Publish failed: {e}", exc_info=True)

    async def close(self):
        if self._connected:
            await self.rabbit.close()
            self._connected = False
