import json

from reforma_report.infrastructure.config.rabbitmq_config import RABBITMQ_HOST
from reforma_report.infrastructure.rabbitmq.connection import RabbitMQConnection
from reforma_report.infrastructure.config.rabbitmq_config import RABBITMQ_PORT
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
            try:
                await self.rabbit.connect()
                self._connected = True

                log_info(
                    "RabbitMQ connection established for event publisher",
                    service="auth-service",
                    context={
                        "rabbitmq_host": RABBITMQ_HOST,
                        "rabbitmq_port": RABBITMQ_PORT
                    }
                )
            except Exception as e:
                log_error(
                    "Failed to establish RabbitMQ connection for event publisher",
                    service="auth-service",
                    context={
                        "rabbitmq_host": RABBITMQ_HOST,
                        "rabbitmq_port": RABBITMQ_PORT,
                        "error_detail": str(e)
                    }
                )
                raise

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

            payload_size = len(json.dumps(message).encode())

            log_info(
                "Publishing event to RabbitMQ",
                service="auth-service",
                context={
                    "exchange": exchange_name,
                    "event_type": event_type,
                    "routing_key": routing,
                    "payload_size_bytes": payload_size,
                    "payload_keys": list(payload.keys())
                }
            )

            await self.rabbit.publish(exchange_name, routing, message)

            log_info(
                "Event published successfully",
                service="auth-service",
                context={
                    "exchange": exchange_name,
                    "event_type": event_type,
                    "routing_key": routing,
                    "payload_size_bytes": payload_size
                }
            )

        except Exception as e:
            log_error(
                "Failed to publish event to RabbitMQ",
                service="auth-service",
                context={
                    "exchange": exchange_name,
                    "event_type": event_type,
                    "routing_key": routing,
                    "payload_size_bytes": len(json.dumps(message).encode()) if 'message' in locals() else 0,
                    "error_detail": str(e)
                }
            )
            raise

    async def close(self):
        if self._connected:
            try:
                await self.rabbit.close()
                self._connected = False

                log_info(
                    "RabbitMQ connection closed for event publisher",
                    service="auth-service"
                )
            except Exception as e:
                log_error(
                    "Error while closing RabbitMQ connection for event publisher",
                    service="auth-service",
                    context={"error_detail": str(e)}
                )