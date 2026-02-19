import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from reforma_payment.infrastructure.db.session import create_database, init_models
from reforma_payment.presentation.api.payments.webhooks import event_publisher
from reforma_common.logger import log_info, log_error
from reforma_payment.presentation.api.payments.payments import router as payments_router
from reforma_payment.presentation.api.payments.webhooks import router as webhooks_router

async def wait_for_rabbitmq(retries: int = 20, delay: int = 10):
    for attempt in range(1, retries + 1):
        try:
            await event_publisher.connect()
            log_info("RabbitMQ подключен!", service="auth-service")
            return
        except Exception as e:
            log_info(f"RabbitMQ недоступен, попытка {attempt}/{retries}: {e}", service="auth-service")
            await asyncio.sleep(delay)
    raise RuntimeError("Не удалось подключиться к RabbitMQ после нескольких попыток")

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_database()
    await init_models()
    await wait_for_rabbitmq()
    yield

app = FastAPI(title="Payment Service", lifespan=lifespan)

app.include_router(payments_router)
app.include_router(webhooks_router)