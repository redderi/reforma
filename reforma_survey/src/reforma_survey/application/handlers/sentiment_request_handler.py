from uuid import UUID, uuid4
from typing import List, Dict, Any
from datetime import datetime

from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.config.rabbitmq_config import MODEL_EXCHANGE, SENTIMENT_BATCH_ANSWERS_ROUTING_KEY
from reforma_survey.infrastructure.rabbitmq.publisher import EventPublisher
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class SentimentRequestHandler:

    def __init__(
        self,
        response_repository: ResponseRepository,
        publisher: EventPublisher,
    ):
        self.response_repository = response_repository
        self.publisher = publisher

    async def handle(self, payload: Dict[str, Any]) -> None:
        try:
            question_stats_id_str = payload.get("question_stats_id")
            question_id_str = payload.get("question_id")
            survey_id_str = payload.get("survey_id")

            if not all([question_stats_id_str, question_id_str, survey_id_str]):
                log_error(
                    "Missing required fields in sentiment request payload",
                    extra={"payload": payload},
                )
                return

            question_stats_id = UUID(question_stats_id_str)
            question_id = UUID(question_id_str)
            survey_id = UUID(survey_id_str)

            survey_stat_id_str = payload.get("survey_stat_id")
            survey_stat_id = UUID(survey_stat_id_str) if survey_stat_id_str else None

            log_info(
                "Processing sentiment request",
                extra={
                    "question_stats_id": question_stats_id_str,
                    "question_id": question_id_str,
                    "survey_id": survey_id_str,
                    "survey_stat_id": survey_stat_id_str,
                }
            )

            async with SessionLocal() as db:
                async with db.begin():
                    texts: List[str] = await self.response_repository.get_answers_for_question(
                        survey_id=survey_id,
                        question_id=question_id,
                        include_anonymous=True,
                    )

                    BATCH_SIZE = 32

                    if not texts:
                        log_info(
                            "No text answers found for question",
                            extra={
                                "survey_id": survey_id_str,
                                "question_id": question_id_str,
                            }
                        )

                    log_info(
                        f"Extracted {len(texts)} text answers for question",
                        extra={
                            "question_id": question_id_str,
                            "survey_id": survey_id_str,
                            "text_count": len(texts),
                        }
                    )

                    total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE

                    for batch_idx in range(total_batches):
                        start = batch_idx * BATCH_SIZE
                        end = start + BATCH_SIZE
                        batch_texts = texts[start:end]

                        await self.publisher.publish_event(
                            exchange=MODEL_EXCHANGE,
                            routing_key=SENTIMENT_BATCH_ANSWERS_ROUTING_KEY,
                            payload={
                                "question_stats_id": question_stats_id_str,
                                "question_id": question_id_str,
                                "survey_id": survey_id_str,
                                "survey_stat_id": survey_stat_id_str,
                                "batch_id": str(uuid4()),
                                "batch_index": batch_idx,
                                "total_batches": total_batches,
                                "texts": batch_texts,
                                "timestamp": datetime.utcnow().isoformat(),
                                # "correlation_id": payload.get("correlation_id"),
                            }
                        )

                        log_info(
                            f"Published batch {batch_idx + 1}/{total_batches}",
                            extra={"question_stats_id": question_stats_id_str, "batch_size": len(batch_texts)}
                        )

        except Exception as e:
            log_error(
                "Failed to process sentiment request",
                extra={
                    "payload": payload,
                    "error": str(e),
                },
                exc_info=True
            )
            # await self.publisher.publish_event(
            #     exchange="reforma.events",
            #     routing_key="question.sentiment.failed",
            #     payload={
            #         "question_stats_id": question_stats_id_str,
            #         "question_id": question_id_str,
            #         "survey_id": survey_id_str,
            #         "error": str(e),
            #         "stage": "survey_answers_collection",
            #     }
            # )