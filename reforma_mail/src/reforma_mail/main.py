from fastapi import FastAPI
from contextlib import asynccontextmanager
from reforma_common.trace_middleware import TraceMiddleware
from reforma_mail.infrastructure.rabbitmq.consumer import MailConsumer
from reforma_mail.presentation.api.mail import router as mail_router
import asyncio
from reforma_common.logger import log_info, log_error, log_warning
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
                log_info(
                    "Elasticsearch connection established",
                    service="mail-service",
                    context={
                        "attempt": attempt,
                        "max_retries": retries,
                        "delay_seconds": delay,
                    },
                )
                return
        except Exception as e:
            log_warning(
                "Elasticsearch connection attempt failed",
                service="mail-service",
                context={
                    "attempt": attempt,
                    "max_retries": retries,
                    "delay_seconds": delay,
                    "error_detail": str(e),
                },
            )
        await asyncio.sleep(delay)
    log_error(
        "Failed to connect to Elasticsearch after all retries",
        service="mail-service",
        context={"attempts_made": retries, "delay_seconds": delay},
    )
    await es_client.close()
    raise RuntimeError("Failed to connect to Elasticsearch after multiple attempts")


async def wait_for_rabbitmq(retries: int = 20, delay: int = 10):
    for attempt in range(1, retries + 1):
        try:
            await mail_consumer.connect()
            log_info(
                "RabbitMQ connection established",
                service="mail-service",
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
                service="mail-service",
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
        service="mail-service",
        context={"attempts_made": retries, "delay_seconds": delay},
    )
    raise RuntimeError("Failed to connect to RabbitMQ after multiple attempts")


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
app.add_middleware(TraceMiddleware)
app.include_router(mail_router)
