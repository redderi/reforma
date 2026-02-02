from sqlalchemy import String, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timedelta
from reforma_authorization.infrastructure.db.base import Base


class UserModel(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, index=True, unique=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    refresh_tokens: Mapped[list["RefreshTokenModel"]] = relationship(
        "RefreshTokenModel", back_populates="user", cascade="all, delete-orphan"
    )
    email_tokens: Mapped[list["EmailVerificationTokenModel"]] = relationship(
        "EmailVerificationTokenModel", back_populates="user", cascade="all, delete-orphan"
    )


class RefreshTokenModel(Base):
    __tablename__ = "refresh_token"

    token: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    device_id: Mapped[str] = mapped_column(String)
    expires_at: Mapped[datetime] = mapped_column(DateTime)

    user: Mapped[UserModel] = relationship("UserModel", back_populates="refresh_tokens")


class EmailVerificationTokenModel(Base):
    __tablename__ = "email_verification_token"

    token: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    expires_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24))

    user: Mapped[UserModel] = relationship("UserModel", back_populates="email_tokens")
