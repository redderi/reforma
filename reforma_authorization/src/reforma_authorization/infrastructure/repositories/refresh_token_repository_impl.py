from datetime import datetime
from reforma_authorization.domain.repositories.refresh_token_repository import RefreshTokenRepository
from sqlalchemy.orm import Session
from reforma_authorization.domain.entities.refresh_token import RefreshToken
from reforma_authorization.infrastructure.db.models import RefreshTokenModel

class RefreshTokenRepositoryImpl(RefreshTokenRepository):

    def __init__(self, db: Session):
        self.db = db

    def save(self, token: RefreshToken) -> None:
        self.db.add(
            RefreshTokenModel(
                token = token.token,
                user_id = token.user_id,
                device_id = token.device_id,
                expires_at = token.expires_at
            )
        )
        self.db.commit()

    def get(self, token:str) -> RefreshToken | None:
        obj = self.db.get(RefreshTokenModel, token)
        if not obj or obj.expires_at < datetime.utcnow():
            return None
        return RefreshToken(
            token=obj.token,
            user_id=obj.user_id,
            device_id=obj.device_id,
            expires_at=obj.expires_at
        )
    
    def delete(self, token:str) -> None:
        self.db.query(RefreshTokenModel).filter_by(token=token).delete()
        self.db.commit()

    def delete_by_user_and_device(self, user_id: int, device_id: str) -> None:
        self.db.query(RefreshTokenModel).filter_by(
            user_id=user_id,
            device_id=device_id
        ).delete()
        self.db.commit()

    def delete_all_by_user(self, user_id: int) -> None:
        self.db.query(RefreshTokenModel).filter_by(
            user_id=user_id
        ).delete()
        self.db.commit()
