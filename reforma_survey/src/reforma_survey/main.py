from fastapi import FastAPI
from contextlib import asynccontextmanager
from reforma_survey.infrastructure.rabbitmq.consumer import UserConsumer
from reforma_survey.presentation.api.user_profile import router as user_profile_router
from reforma_survey.presentation.api.survey import router as survey_router
from reforma_survey.presentation.api.question import router as question_router
from reforma_survey.presentation.api.response import router as response_router
from reforma_survey.presentation.api.balance import router as balance_router
from reforma_survey.presentation.api.branching_rule import router as branching_rule_router
from reforma_survey.presentation.api.report import router as report_router
from reforma_survey.presentation.api.template import router as template_router
from reforma_survey.presentation.api.storage import router as storage_router
from reforma_survey.presentation.api.internal.response import router as internal_response_router
from reforma_survey.presentation.api.internal.question import router as internal_question_router

import asyncio
from reforma_common.logger import log_info, log_warning, log_error
from elasticsearch import AsyncElasticsearch
from reforma_survey.infrastructure.db.session import create_database, init_models

from reforma_common.trace_middleware import TraceMiddleware


user_consumer = UserConsumer()
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
                    service="survey-service",
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
                service="survey-service",
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
        service="survey-service",
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
            await user_consumer.connect()
            log_info(
                "RabbitMQ connection established",
                service="survey-service",
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
                service="survey-service",
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
        service="survey-service",
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
            "Starting survey service initialization",
            service="survey-service"
        )

        create_database()
        log_info(
            "Database creation/verification completed",
            service="survey-service"
        )

        await init_models()
        log_info(
            "Database models initialized successfully",
            service="survey-service"
        )

        await wait_for_rabbitmq()
        log_info(
            "RabbitMQ initialization completed",
            service="survey-service"
        )

        global consumer_task
        consumer_task = asyncio.create_task(user_consumer.start_consuming())

        log_info(
            "User consumer task started",
            service="survey-service"
        )

        yield

    finally:
        if consumer_task:
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                pass

        await user_consumer.close()

        if es_client:
            await es_client.close()

        log_info(
            "Survey service shutdown completed",
            service="survey-service"
        )


app = FastAPI(title="Survey Service", lifespan=lifespan)
app.add_middleware(TraceMiddleware)
app.include_router(survey_router)
app.include_router(user_profile_router)
app.include_router(question_router)
app.include_router(response_router)
app.include_router(balance_router)
app.include_router(branching_rule_router)
app.include_router(report_router)
app.include_router(template_router)
app.include_router(storage_router)
app.include_router(internal_response_router)
app.include_router(internal_question_router)