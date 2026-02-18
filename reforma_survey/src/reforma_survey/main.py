from fastapi import FastAPI
from contextlib import asynccontextmanager
from reforma_survey.infrastructure.rabbitmq.consumer import UserConsumer
from reforma_survey.presentation.api.survey import router as survay_router
from reforma_survey.presentation.api.user_profile import router as user_router
import asyncio
from reforma_common.logger import log_info, log_error
from elasticsearch import AsyncElasticsearch
from reforma_survey.infrastructure.db.session import create_database, init_models


user_consumer = UserConsumer()
consumer_task: asyncio.Task | None = None

es_client: AsyncElasticsearch | None = None

async def wait_for_elasticsearch(retries: int = 20, delay: int = 10):
    global es_client
    es_client = AsyncElasticsearch(hosts=["http://elasticsearch:9200"])
    for attempt in range(1, retries + 1):
        try:
            if await es_client.ping():
                log_info("Elasticsearch подключен!", service="survey-service")
                return
        except Exception as e:
            log_info(f"Elasticsearch недоступен, попытка {attempt}/{retries}: {e}", service="survey-service")
        await asyncio.sleep(delay)
    await es_client.close()
    raise RuntimeError("Не удалось подключиться к Elasticsearch после нескольких попыток")

async def wait_for_rabbitmq(retries: int = 20, delay: int = 10):
    for attempt in range(1, retries + 1):
        try:
            await user_consumer.connect()
            log_info("RabbitMQ подключен!", service="survey-service")
            return
        except Exception as e:
            log_info(f"RabbitMQ недоступен, попытка {attempt}/{retries}: {e}", service="survey-service")
            await asyncio.sleep(delay)
    raise RuntimeError("Не удалось подключиться к RabbitMQ после нескольких попыток")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        create_database()
        await init_models()
        await wait_for_rabbitmq()
        global consumer_task
        consumer_task = asyncio.create_task(user_consumer.start_consuming())

        yield
    finally:
        if consumer_task:
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                pass
        await user_consumer.close()

app = FastAPI(title="Survey Service", lifespan=lifespan)
app.include_router(survay_router)
app.include_router(user_router)
