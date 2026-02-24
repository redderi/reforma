# reforma_report/infrastructure/db/models.py
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, JSON, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ARRAY
from sqlalchemy.orm import mapped_column, Mapped, relationship
from reforma_report.infrastructure.db.base import Base


class SurveyStatModel(Base):
    __tablename__ = "survey_stat"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, unique=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    allowed_user_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(PG_UUID(as_uuid=True)), default=list, nullable=False)

    total_responses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Агрегаты по типам вопросов
    sum_per_type: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    sum_of_squares_per_type: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    min_per_type: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    max_per_type: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Поля для хранения результатов ИИ
    sentiment_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    keyword_analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    recommendations: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Связь с вопросами
    questions: Mapped[list["QuestionStatModel"]] = relationship(
        "QuestionStatModel", back_populates="survey", cascade="all, delete-orphan"
    )


class QuestionStatModel(Base):
    __tablename__ = "question_stat"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_stat_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("survey_stat.id", ondelete="CASCADE"),
        nullable=False
    )
    question_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)

    total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sum: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    sum_of_squares: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    min: Mapped[float | None] = mapped_column(Float, nullable=True)
    max: Mapped[float | None] = mapped_column(Float, nullable=True)
    distribution: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Связь с опросом
    survey: Mapped[SurveyStatModel] = relationship("SurveyStatModel", back_populates="questions")