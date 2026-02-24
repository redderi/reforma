from typing import Any
from reforma_report.application.handles.question_handler import QuestionHandler
from reforma_report.domain.entities.question_stats import QuestionStats


class ScaleHandler(QuestionHandler):
    async def handle(self, stats: QuestionStats, value: Any):
        try:
            numeric_value = float(value)
            stats.sum += numeric_value
            stats.sum_of_squares += numeric_value ** 2
            stats.min = numeric_value if stats.min is None else min(stats.min, numeric_value)
            stats.max = numeric_value if stats.max is None else max(stats.max, numeric_value)
        except (ValueError, TypeError):
            stats.distribution[str(value)] = stats.distribution.get(str(value), 0) + 1