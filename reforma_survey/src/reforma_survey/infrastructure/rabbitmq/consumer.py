import json
import aio_pika
from reforma_survey.infrastructure.config.rabbitmq_config import ADD_BALANCE_ROUTING_KEY
from reforma_survey.infrastructure.rabbitmq.connection import RabbitMQConnection
from reforma_survey.infrastructure.config.rabbitmq_config import (
    USER_EXCHANGE,
    USER_CREATE_ROUTING_KEY,
    USER_DELETE_ROUTING_KEY,
    USER_CHANGE_USERNAME_ROUTING_KEY,
    USER_CHANGE_EMAIL_ROUTING_KEY
)
from reforma_survey.application.handlers.create_user_profile_handler import CreateUserProfileHandler
from reforma_survey.application.handlers.delete_user_profile_handler import DeleteUserProfileHandler
from reforma_survey.application.handlers.change_user_profile_handler import ChangeUserProfileUsernameHandler
from reforma_survey.application.handlers.change_user_profile_email_handler import ChangeUserProfileEmailHandler

from reforma_common.logger import log_info, log_warning, log_error
from reforma_survey.application.handlers.add_balance_handler import AddBalanceHandler

HANDLERS = {
    USER_CREATE_ROUTING_KEY: CreateUserProfileHandler(),
    USER_DELETE_ROUTING_KEY: DeleteUserProfileHandler(),
    USER_CHANGE_USERNAME_ROUTING_KEY: ChangeUserProfileUsernameHandler(),
    USER_CHANGE_EMAIL_ROUTING_KEY: ChangeUserProfileEmailHandler(),
    ADD_BALANCE_ROUTING_KEY: AddBalanceHandler()
}

class UserConsumer:
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

        exchange = await channel.declare_exchange(
            USER_EXCHANGE,
            aio_pika.ExchangeType.DIRECT,
            durable=True
        )

        queue_name = "survey_user_events"
        queue = await channel.declare_queue(queue_name, durable=True)

        for rk in HANDLERS.keys():
            await queue.bind(exchange, routing_key=rk)

        log_info("Start Consuming user events", service="survey_service")

        async def callback(message: aio_pika.IncomingMessage):
            async with message.process():
                try:
                    data = json.loads(message.body.decode())
                    event_type = data.get("type")
                    payload = data.get("payload")

                    handler = HANDLERS.get(event_type)
                    if handler:
                        await handler.handle(payload)
                    else:
                        log_warning(f"[UserConsumer] Unknown event type: {event_type}", service="survey_service")
                except Exception as e:
                    log_error(f"[UserConsumer] Error processing message: {e}", service="survey_service")

        await queue.consume(callback)

    async def close(self):
        if self._connected:
            await self.rabbit.close()
            self._connected = False
