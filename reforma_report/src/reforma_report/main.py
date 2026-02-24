from fastapi import FastAPI
from contextlib import asynccontextmanager
from reforma_report.infrastructure.rabbitmq.consumer import ReportConsumer
import asyncio
from reforma_common.logger import log_info, log_warning, log_error
from elasticsearch import AsyncElasticsearch
from reforma_report.infrastructure.db.session import create_database, init_models
from reforma_report.presentation.api.question_stats import router as question_stats_router

from reforma_common.trace_middleware import TraceMiddleware


report_consumer = ReportConsumer()
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
                    service="report-service",
                    context={
                        "attempt": attempt,
                        "max_retries": retries,
                        "delay_seconds": delay
                    }
                )
                return
        except Exception as e:
            log_warning(
                "Elasticsearch connection attempt failed",
                service="report-service",
                context={
                    "attempt": attempt,
                    "max_retries": retries,
                    "delay_seconds": delay,
                    "error_detail": str(e)
                }
            )
        await asyncio.sleep(delay)

    log_error(
        "Failed to connect to Elasticsearch after all retries",
        service="report-service",
        context={
            "attempts_made": retries,
            "delay_seconds": delay
        }
    )
    await es_client.close()
    raise RuntimeError("Failed to connect to Elasticsearch after multiple attempts")


async def wait_for_rabbitmq(retries: int = 20, delay: int = 10):
    for attempt in range(1, retries + 1):
        try:
            await report_consumer.connect()
            log_info(
                "RabbitMQ connection established",
                service="report-service",
                context={
                    "attempt": attempt,
                    "max_retries": retries,
                    "delay_seconds": delay
                }
            )
            return
        except Exception as e:
            log_warning(
                "RabbitMQ connection attempt failed",
                service="report-service",
                context={
                    "attempt": attempt,
                    "max_retries": retries,
                    "delay_seconds": delay,
                    "error_detail": str(e)
                }
            )
            await asyncio.sleep(delay)

    log_error(
        "Failed to connect to RabbitMQ after all retries",
        service="report-service",
        context={
            "attempts_made": retries,
            "delay_seconds": delay
        }
    )
    raise RuntimeError("Failed to connect to RabbitMQ after multiple attempts")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        log_info(
            "Starting report service initialization",
            service="report-service"
        )

        create_database()
        log_info(
            "Database creation/verification completed",
            service="report-service"
        )

        await init_models()
        log_info(
            "Database models initialized successfully",
            service="report-service"
        )

        await wait_for_rabbitmq()
        log_info(
            "RabbitMQ initialization completed",
            service="report-service"
        )

        global consumer_task
        consumer_task = asyncio.create_task(report_consumer.start_consuming())

        log_info(
            "User consumer task started",
            service="report-service"
        )

        yield

    finally:
        if consumer_task:
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                pass

        await report_consumer.close()

        if es_client:
            await es_client.close()

        log_info(
            "Report service shutdown completed",
            service="report-service"
        )


app = FastAPI(title="Report Service", lifespan=lifespan)
app.add_middleware(TraceMiddleware)
app.include_router(question_stats_router)