import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from reforma_common.trace_middleware import TraceMiddleware
from reforma_payment.infrastructure.db.session import create_database, init_models
from reforma_common.logger import log_info, log_warning, log_error
from reforma_payment.presentation.api.payments.payments import router as payments_router
from reforma_payment.presentation.api.payments.webhooks import router as webhooks_router
from reforma_payment.presentation.dependencies.get_event_publisher import (
    get_event_publisher,
)


async def wait_for_rabbitmq(retries: int = 20, delay: int = 10):
    for attempt in range(1, retries + 1):
        try:
            event_publisher = get_event_publisher()
            await event_publisher.connect()

            log_info(
                "RabbitMQ connection established",
                service="payment-service",
                context={
                    "attempt": attempt,
                    "max_retries": retries,
                    "delay_seconds": delay,
                },
            )
            return

        except Exception as e:
            log_warning(
                "RabbitMQ connection attempt failed",
                service="payment-service",
                context={
                    "attempt": attempt,
                    "max_retries": retries,
                    "delay_seconds": delay,
                    "error_detail": str(e),
                },
            )
            await asyncio.sleep(delay)

    log_error(
        "Failed to connect to RabbitMQ after all retries",
        service="payment-service",
        context={"attempts_made": retries, "delay_seconds": delay},
    )
    raise RuntimeError("Failed to connect to RabbitMQ after multiple attempts")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        log_info("Starting payment service initialization", service="payment-service")
        create_database()
        log_info("Database creation/verification completed", service="payment-service")
        await init_models()
        log_info("Database models initialized successfully", service="payment-service")
        await wait_for_rabbitmq()
        log_info("RabbitMQ initialization completed", service="payment-service")
        yield
    finally:
        event_publisher = get_event_publisher()
        await event_publisher.close()
        log_info("Payment service shutdown completed", service="payment-service")


app = FastAPI(title="Payment Service", lifespan=lifespan)
app.add_middleware(TraceMiddleware)
app.include_router(payments_router)
app.include_router(webhooks_router)
