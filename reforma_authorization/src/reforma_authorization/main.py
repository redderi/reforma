import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from reforma_authorization.presentation.api.auth import router as auth_router
from reforma_authorization.presentation.api.user import router as user_router
from reforma_authorization.presentation.api.admin import router as admin_router
from reforma_authorization.infrastructure.db.session import create_database, create_initial_admin, init_models
from reforma_authorization.presentation.api.auth import event_publisher
from reforma_common.logger import log_info, log_error

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
    await create_initial_admin()
    await wait_for_rabbitmq()
    yield
    await event_publisher.close()

app = FastAPI(title="Auth Service", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(admin_router)
