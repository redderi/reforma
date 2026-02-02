from datetime import datetime
from sqlalchemy.orm import Session
from reforma_authorization.domain.entities.user import User
from reforma_authorization.infrastructure.db.models import EmailVerificationTokenModel
import secrets

class EmailTokenRepositoryImpl:
    def __init__(self, db: Session):
        self.db = db

    def create_token(self, user_id: int) -> str:
        token = secrets.token_urlsafe(32)
        model = EmailVerificationTokenModel(user_id=user_id, token=token)
        self.db.add(model)
        self.db.commit()
        return token

    def get_valid_user_id_by_token(self, token: str) -> int | None:
        model = self.db.query(EmailVerificationTokenModel)\
                    .filter_by(token=token)\
                    .first()
        if not model or model.expires_at < datetime.utcnow():
            return None
        return model.user_id

    def delete_token(self, token: str) -> None:
        self.db.query(EmailVerificationTokenModel).filter_by(token=token).delete()
        self.db.commit()
