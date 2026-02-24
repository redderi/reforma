from typing import Any
from reforma_report.domain.entities.question_stats import QuestionStats


class QuestionHandler:
    async def handle(self, stats: QuestionStats, value: Any):
        raise NotImplementedError()
