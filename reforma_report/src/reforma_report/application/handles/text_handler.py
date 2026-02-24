from typing import Any
from reforma_report.application.handles.question_handler import (
    QuestionHandler,
)
from reforma_report.domain.entities.question_stats import (
    QuestionStats,
)


class TextHandler(QuestionHandler):
    async def handle(self, stats: QuestionStats, value: Any):
        stats.distribution[str(value)] = stats.distribution.get(str(value), 0) + 1
