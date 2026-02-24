from reforma_survey.domain.entities.question import Question
from reforma_survey.domain.repositories.question_repository import QuestionRepository
from reforma_survey.infrastructure.db.models import QuestionModel
from reforma_survey.infrastructure.db.session import SessionLocal
from sqlalchemy import select, func


class CreateQuestionUseCase:
    def __init__(self, repository: QuestionRepository):
        self.repository = repository

    async def execute(self, question: Question) -> Question:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    stmt = select(func.max(QuestionModel.order)).where(
                        QuestionModel.survey_id == question.survey_id
                    )
                    result = await db.execute(stmt)
                    max_order = result.scalar()
                    next_order = (max_order or 0) + 1

                    question_with_order = Question(
                        id=question.id,
                        survey_id=question.survey_id,
                        text=question.text,
                        type=question.type,
                        options=question.options,
                        style=question.style,
                        order=next_order,
                    )

                    created = await self.repository.create(question_with_order)

                    return created

                except Exception:
                    await db.rollback()
                    raise
