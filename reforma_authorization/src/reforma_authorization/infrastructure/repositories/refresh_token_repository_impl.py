from datetime import datetime
from sqlalchemy.orm import Session

from reforma_authorization.domain.repositories.refresh_token_repository import RefreshTokenRepository
from reforma_authorization.domain.entities.refresh_token import RefreshToken
from reforma_authorization.infrastructure.db.models import RefreshTokenModel


class RefreshTokenRepositoryImpl(RefreshTokenRepository):

    def __init__(self, db: Session):
        self.db = db

    def _to_entity(self, model: RefreshTokenModel) -> RefreshToken:
        return RefreshToken(
            token=model.token,
            user_id=model.user_id,
            device_id=model.device_id,
            expires_at=model.expires_at,
        )


    def save(self, token: RefreshToken) -> RefreshToken:
        model = RefreshTokenModel(
            token=token.token,
            user_id=token.user_id,
            device_id=token.device_id,
            expires_at=token.expires_at,
        )

        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)

        return self._to_entity(model)

    def delete(self, token: str) -> None:
        model = self.db.query(RefreshTokenModel).filter_by(token=token).first()
        if model:
            self.db.delete(model)
            self.db.commit()

    def delete_by_user_and_device(self, user_id: int, device_id: str) -> None:
        tokens = self.db.query(RefreshTokenModel).filter_by(
            user_id=user_id,
            device_id=device_id,
        ).all()

        for model in tokens:
            self.db.delete(model)

        self.db.commit()

    def delete_all_by_user(self, user_id: int) -> None:
        tokens = self.db.query(RefreshTokenModel).filter_by(user_id=user_id).all()

        for model in tokens:
            self.db.delete(model)

        self.db.commit()

    def get(self, token: str) -> RefreshToken | None:
        model = self.db.query(RefreshTokenModel).filter_by(token=token).first()

        if not model:
            return None

        if model.expires_at < datetime.utcnow():
            return None

        return self._to_entity(model)
