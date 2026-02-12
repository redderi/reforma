import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from reforma_authorization.presentation.api.auth import router as auth_router
from reforma_authorization.presentation.api.user import router as user_router
from reforma_authorization.infrastructure.db.session import create_database
from reforma_authorization.presentation.api.auth import mail_publisher
from reforma_authorization.common.logger import log_info, log_error
from elasticsearch import AsyncElasticsearch

es_client = AsyncElasticsearch(hosts=["http://elasticsearch:9200"])


async def wait_for_rabbitmq(retries: int = 20, delay: int = 10):
    for attempt in range(1, retries + 1):
        try:
            await mail_publisher.connect()
            log_info("RabbitMQ подключен!", service="auth-service")
            return
        except Exception as e:
            log_info(f"RabbitMQ недоступен, попытка {attempt}/{retries}: {e}", service="auth-service")
            await asyncio.sleep(delay)
    raise RuntimeError("Не удалось подключиться к RabbitMQ после нескольких попыток")

async def wait_for_elasticsearch(retries: int = 20, delay: int = 10):
    for attempt in range(1, retries + 1):
        try:
            if await es_client.ping():
                log_info("Elasticsearch подключен!", service="auth-service")
                return
        except Exception as e:
            log_info(f"Elasticsearch недоступен, попытка {attempt}/{retries}: {e}", service="auth-service")
        await asyncio.sleep(delay)
    raise RuntimeError("Не удалось подключиться к Elasticsearch после нескольких попыток")


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_database()
    await wait_for_rabbitmq()
    # await asyncio.gather(
    #     wait_for_rabbitmq(),
    #     wait_for_elasticsearch()
    # )

    yield
    await mail_publisher.close()

app = FastAPI(title="Auth Service", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(user_router)
