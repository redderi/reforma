from datetime import datetime, timedelta
import secrets
from sqlalchemy.orm import Session

from reforma_authorization.domain.repositories.email_verification_token import EmailVerificationTokenRepository
from reforma_authorization.domain.entities.email_verification_token import EmailVerificationToken
from reforma_authorization.infrastructure.db.models import EmailVerificationTokenModel


class EmailTokenRepositoryImpl(EmailVerificationTokenRepository):

    def __init__(self, db: Session):
        self.db = db

    def _to_entity(self, model: EmailVerificationTokenModel) -> EmailVerificationToken:
        return EmailVerificationToken(
            user_id=model.user_id,
            token=model.token,
            expires_at=model.expires_at,
        )

    def save(self, token: EmailVerificationToken) -> EmailVerificationToken:
        model = EmailVerificationTokenModel(
            user_id=token.user_id,
            token=token.token,
            expires_at=token.expires_at,
        )

        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)

        return self._to_entity(model)

    def delete(self, token_str: str) -> None:
        model = self.db.query(EmailVerificationTokenModel).filter_by(token=token_str).first()

        if model:
            self.db.delete(model)
            self.db.commit()


    def get(self, token_str: str) -> EmailVerificationToken | None:
        model = self.db.query(EmailVerificationTokenModel).filter_by(token=token_str).first()

        if not model:
            return None

        if model.expires_at < datetime.utcnow():
            return None

        return self._to_entity(model)


    def create_token(self, user_id: int, hours_valid: int = 24) -> EmailVerificationToken:
        token_str = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=hours_valid)

        token = EmailVerificationToken(
            user_id=user_id,
            token=token_str,
            expires_at=expires_at,
        )

        return self.save(token)
