from datetime import datetime
from uuid import UUID
from typing import Dict, Any
from reforma_report.domain.entities.question_stats import QuestionStats
from reforma_report.domain.repositories.question_stats_repository import (
    QuestionStatsRepository,
)
from reforma_report.application.handles.choice_handler import (
    ChoiceHandler,
)
from reforma_report.application.handles.scale_handler import (
    ScaleHandler,
)
from reforma_report.application.handles.text_handler import (
    TextHandler,
)


QUESTION_TYPE_HANDLERS = {
    "scale": ScaleHandler(),
    "single_choice": ChoiceHandler(),
    "multiple_choice": ChoiceHandler(),
    "text": TextHandler(),
}


class IncrementalUpdater:
    def __init__(self, repository: QuestionStatsRepository):
        self.repository = repository

    async def consume(
        self,
        survey_id: UUID,
        answers_batch: list[Dict[UUID, Any]],
        question_types: Dict[UUID, str], 
    ) -> None:
        for answers in answers_batch:
            for question_id, value in answers.items():
                q_type = question_types.get(question_id, "text")  

                stats = await self.repository.get(survey_id, question_id)
                if not stats:
                    stats = QuestionStats(
                        survey_id=survey_id,
                        question_id=question_id,
                        type=q_type,
                    )

                stats.total += 1

                handler = QUESTION_TYPE_HANDLERS.get(q_type, TextHandler())
                await handler.handle(stats, value)

                stats.updated_at = datetime.utcnow()
                await self.repository.upsert(stats)
