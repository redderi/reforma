import json
import aio_pika
from reforma_report.infrastructure.config.rabbitmq_config import RESPONSE_SUBMITTED_ROUTING_KEY
from reforma_report.infrastructure.config.rabbitmq_config import REPORT_EXCHANGE
from reforma_report.infrastructure.rabbitmq.connection import RabbitMQConnection
from reforma_common.logger import log_info, log_warning, log_error
from reforma_report.application.handles.response_submitted import ResponseSubmitted

HANDLERS = {
    RESPONSE_SUBMITTED_ROUTING_KEY: ResponseSubmitted()
}


class ReportConsumer:
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
            REPORT_EXCHANGE, aio_pika.ExchangeType.DIRECT, durable=True
        )

        queue_name = "report_user_events"
        queue = await channel.declare_queue(queue_name, durable=True)

        for rk in HANDLERS.keys():
            await queue.bind(exchange, routing_key=rk)

        log_info("Start Consuming report events", service="report_service")

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
                        log_warning(
                            f"[ReportConsumer] Unknown event type: {event_type}",
                            service="report_service",
                        )
                except Exception as e:
                    log_error(
                        f"[ReportConsumer] Error processing message: {e}",
                        service="report_service",
                    )

        await queue.consume(callback)

    async def close(self):
        if self._connected:
            await self.rabbit.close()
            self._connected = False
