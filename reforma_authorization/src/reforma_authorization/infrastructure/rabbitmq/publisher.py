import asyncio
import json
from reforma_authorization.infrastructure.rabbitmq.connection import RabbitMQConnection

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

    async def publish(self, message: dict, routing_key: str = "mail_queue"):
        if not self._connected:
            await self.connect()
        await self.rabbit.publish("mail_exchange", routing_key, message)

    async def close(self):
        if self._connected:
            await self.rabbit.close()
            self._connected = False
