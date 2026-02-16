from fastapi import FastAPI
from contextlib import asynccontextmanager
from reforma_mail.infrastructure.rabbitmq.consumer import MailConsumer
from reforma_mail.presentation.api.mail import router as mail_router
import asyncio
from reforma_common.logger import log_info, log_error
from elasticsearch import AsyncElasticsearch

mail_consumer = MailConsumer()
consumer_task: asyncio.Task | None = None
es_client: AsyncElasticsearch | None = None

async def wait_for_elasticsearch(retries: int = 20, delay: int = 10):
    global es_client
    es_client = AsyncElasticsearch(hosts=["http://elasticsearch:9200"])
    for attempt in range(1, retries + 1):
        try:
            if await es_client.ping():
                log_info("Elasticsearch подключен!", service="mail-service")
                return
        except Exception as e:
            log_info(f"Elasticsearch недоступен, попытка {attempt}/{retries}: {e}", service="mail-service")
        await asyncio.sleep(delay)
    await es_client.close()
    raise RuntimeError("Не удалось подключиться к Elasticsearch после нескольких попыток")

async def wait_for_rabbitmq(retries: int = 20, delay: int = 10):
    for attempt in range(1, retries + 1):
        try:
            await mail_consumer.connect()
            log_info("RabbitMQ подключен!", service="mail-service")
            return
        except Exception as e:
            log_info(f"RabbitMQ недоступен, попытка {attempt}/{retries}: {e}", service="mail-service")
            await asyncio.sleep(delay)
    raise RuntimeError("Не удалось подключиться к RabbitMQ после нескольких попыток")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await wait_for_rabbitmq()
        global consumer_task
        consumer_task = asyncio.create_task(mail_consumer.start_consuming())

        yield
    finally:
        if consumer_task:
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                pass
        await mail_consumer.close()
        if es_client:
            await es_client.close()

app = FastAPI(title="Mail Service", lifespan=lifespan)
app.include_router(mail_router)
