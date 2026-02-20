import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from reforma_authorization.presentation.api.auth import router as auth_router
from reforma_authorization.presentation.api.user import router as user_router
from reforma_authorization.presentation.api.admin import router as admin_router
from reforma_authorization.infrastructure.db.session import (
    create_database,
    create_initial_admin,
    init_models,
)
from reforma_authorization.presentation.dependencies.get_event_publisher import (
    get_event_publisher,
)
from reforma_common.logger import log_error, log_info, log_warning
from reforma_common.trace_middleware import TraceMiddleware


async def wait_for_rabbitmq(retries: int = 20, delay: int = 10):
    for attempt in range(1, retries + 1):
        try:
            event_publisher = get_event_publisher()
            await event_publisher.connect()

            log_info(
                "RabbitMQ connection established successfully",
                service="auth-service",
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
                service="auth-service",
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
        service="auth-service",
        context={"attempts_made": retries, "delay_seconds": delay},
    )
    raise RuntimeError("Failed to connect to RabbitMQ after multiple attempts")


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_database()
    await init_models()
    await create_initial_admin()
    await wait_for_rabbitmq()
    yield
    event_publisher = get_event_publisher()
    await event_publisher.close()


app = FastAPI(title="Auth Service", lifespan=lifespan)
app.add_middleware(TraceMiddleware)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(admin_router)
