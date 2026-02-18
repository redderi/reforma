# reforma_survey/infrastructure/db/models.py

import uuid
from datetime import datetime, date

from sqlalchemy import (
    Column, String, Text, JSON, DateTime, Integer, ForeignKey, Boolean,
    Date
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column, Index

from reforma_survey.infrastructure.db.base import Base


class UserProfileModel(Base):
    __tablename__ = "user_profile"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    profile_picture: Mapped[str | None] = mapped_column(String, nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)

    gender: Mapped[str | None] = mapped_column(String, nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    country: Mapped[str | None] = mapped_column(String, nullable=True)
    city: Mapped[str | None] = mapped_column(String, nullable=True)

    surveys: Mapped[list["SurveyModel"]] = relationship(
        "SurveyModel", back_populates="owner", cascade="all, delete-orphan"
    )
    templates: Mapped[list["TemplateModel"]] = relationship(
        "TemplateModel", back_populates="owner", cascade="all, delete-orphan"
    )
    reports: Mapped[list["ReportModel"]] = relationship(
        "ReportModel", back_populates="owner", cascade="all, delete-orphan"
    )


class TemplateModel(Base):
    __tablename__ = "template"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_profile.id"))
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    style: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    owner: Mapped["UserProfileModel"] = relationship("UserProfileModel", back_populates="templates")
    surveys: Mapped[list["SurveyModel"]] = relationship("SurveyModel", back_populates="template")


class SurveyModel(Base):
    __tablename__ = "survey"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_profile.id"))
    template_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("template.id"), nullable=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner: Mapped["UserProfileModel"] = relationship("UserProfileModel", back_populates="surveys")
    template: Mapped["TemplateModel"] = relationship("TemplateModel", back_populates="surveys")
    questions: Mapped[list["QuestionModel"]] = relationship(
        "QuestionModel", back_populates="survey", cascade="all, delete-orphan"
    )
    responses: Mapped[list["ResponseModel"]] = relationship(
        "ResponseModel", back_populates="survey", cascade="all, delete-orphan"
    )
    reports: Mapped[list["ReportModel"]] = relationship(
        "ReportModel", back_populates="survey", cascade="all, delete-orphan"
    )


class QuestionModel(Base):
    __tablename__ = "question"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("survey.id"))
    question_text: Mapped[str] = mapped_column(Text)
    answer_type: Mapped[str] = mapped_column(String)
    options: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    style: Mapped[dict] = mapped_column(JSON, default=dict)
    
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)

    survey: Mapped["SurveyModel"] = relationship("SurveyModel", back_populates="questions")
    branching_rules: Mapped[list["BranchingRuleModel"]] = relationship(
        "BranchingRuleModel", back_populates="question", cascade="all, delete-orphan"
    )


class BranchingRuleModel(Base):
    __tablename__ = "branching_rule"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("question.id"))
    condition: Mapped[dict] = mapped_column(JSON)

    question: Mapped["QuestionModel"] = relationship("QuestionModel", back_populates="branching_rules")


class ResponseModel(Base):
    __tablename__ = "response"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("survey.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    answers: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    survey: Mapped["SurveyModel"] = relationship("SurveyModel", back_populates="responses")


class ReportModel(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("survey.id"), nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_profile.id"), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    report_type: Mapped[str] = mapped_column(String(20), nullable=False, default="pdf")
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    file_urls: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)

    survey: Mapped["SurveyModel"] = relationship("SurveyModel", back_populates="reports", cascade="all, delete-orphan")
    owner: Mapped["UserProfileModel"] = relationship("UserProfileModel", back_populates="reports", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_reports_survey_status', 'survey_id', 'status'),
        Index('ix_reports_owner_status', 'owner_id', 'status'),
        Index('ix_reports_requested_at', 'requested_at desc'), 
    )