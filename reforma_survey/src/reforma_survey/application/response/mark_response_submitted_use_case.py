from datetime import datetime
from uuid import UUID
from reforma_survey.domain.entities.response import Response
from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.config.rabbitmq_config import REPORT_EXCHANGE, RESPONSE_SUBMITTED_ROUTING_KEY
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_survey.infrastructure.rabbitmq.publisher import EventPublisher


class MarkResponseSubmittedUseCase:
    def __init__(self, repository: ResponseRepository, event_publisher: EventPublisher):
        self.repository = repository
        self.event_publisher = event_publisher

    async def execute(
        self, response_id: UUID, submitted_at: datetime = None
    ) -> Response:
        async with SessionLocal() as db:
            async with db.begin():
                updated = await self.repository.mark_submitted(
                    response_id, submitted_at
                )

                await self.event_publisher.publish_event(
                    exchange_name=REPORT_EXCHANGE,
                    event_type=RESPONSE_SUBMITTED_ROUTING_KEY,
                    payload={
                        "response_id": str(response_id),
                    },
                )

                return updated
