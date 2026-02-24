import aiohttp
from reforma_common.logger import log_info, log_error
from reforma_report.infrastructure.db.session import SessionLocal
from reforma_report.application.incremental_updater_use_case import IncrementalUpdater
from reforma_report.infrastructure.repositories.question_stats_repository_impl import (
    QuestionStatsRepositoryImpl,
)
from reforma_report.infrastructure.config.api_config import INTERNAL_API_KEY, SURVEY_SERVICE_URL


class ResponseSubmitted:
    async def handle(self, payload: dict):
        response_id = payload.get("response_id")
        if not response_id:
            log_error(
                "ResponseSubmitted event missing response_id", service="report_service"
            )
            return

        headers = {"X-API-KEY": INTERNAL_API_KEY}

        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                async with session.get(
                    f"{SURVEY_SERVICE_URL}/responses/{response_id}"
                ) as resp:
                    if resp.status != 200:
                        log_error(
                            f"Failed to fetch response {response_id}, status={resp.status}",
                            service="report_service",
                        )
                        return
                    response_json = await resp.json()

                survey_id = response_json["survey_id"]

                async with session.get(
                    f"{SURVEY_SERVICE_URL}/surveys/{survey_id}/questions"
                ) as resp:
                    if resp.status != 200:
                        log_error(
                            f"Failed to fetch questions for survey {survey_id}, status={resp.status}",
                            service="report_service",
                        )
                        return
                    questions_json = await resp.json()

                question_types = {q["id"]: q["type"] for q in questions_json}

                async with SessionLocal() as db:
                    repository = QuestionStatsRepositoryImpl(db)
                    updater = IncrementalUpdater(repository)

                    answers_batch = [response_json["answers"]]
                    await updater.consume(survey_id, answers_batch, question_types)

                log_info(
                    f"Successfully processed response {response_id}",
                    service="report_service",
                )

            except Exception as e:
                log_error(
                    f"Error processing response_submitted {response_id}: {e}",
                    service="report_service",
                )
