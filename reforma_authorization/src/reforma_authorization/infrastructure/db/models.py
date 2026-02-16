from enum import Enum
from reforma_common.roles import UserRole
from reforma_common.user_status import UserStatus
from sqlalchemy import String, DateTime, ForeignKey, Boolean, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timedelta
from reforma_authorization.infrastructure.db.base import Base
from sqlalchemy.types import Enum as SQLEnum 
import uuid
from sqlalchemy import JSON

class UserModel(Base):
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String, index=True, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, index=True, unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False, default=UserRole.USER.value)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(UserStatus, name="status"),
        nullable=False,
        default=UserStatus.REGISTERED,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    suspension_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    suspended_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    suspender: Mapped["UserModel"] = relationship(
        "UserModel", remote_side=[id], lazy="joined"
    )

    refresh_tokens: Mapped[list["RefreshTokenModel"]] = relationship(
        "RefreshTokenModel",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    email_tokens: Mapped[list["EmailVerificationTokenModel"]] = relationship(
        "EmailVerificationTokenModel",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


class RefreshTokenModel(Base):
    __tablename__ = "refresh_token"

    token: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    device_id: Mapped[str] = mapped_column(String)
    expires_at: Mapped[datetime] = mapped_column(DateTime)

    user: Mapped[UserModel] = relationship("UserModel", back_populates="refresh_tokens")


class EmailVerificationTokenModel(Base):
    __tablename__ = "email_verification_token"

    token: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    expires_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24)
    )
    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    user: Mapped[UserModel] = relationship("UserModel", back_populates="email_tokens")
