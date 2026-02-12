from reforma_authorization.domain.repositories.user_repository import UserRepository
from reforma_authorization.domain.entities.user import User
from reforma_authorization.infrastructure.db.models import UserModel
from sqlalchemy.orm import Session


class UserRepositoryImpl(UserRepository):
    def __init__(self, db: Session):
        self.db = db

    def _to_entity(self, model: UserModel) -> User:
        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            password_hash=model.password_hash,
            is_email_verified=model.is_email_verified
        )

    def get_by_id(self, id: int) -> User | None:
        model = self.db.get(UserModel, id)
        return self._to_entity(model) if model else None

    def get_by_username(self, username: str) -> User | None:
        model = self.db.query(UserModel).filter_by(username=username).first()
        return self._to_entity(model) if model else None

    def get_by_email(self, email: str) -> User | None:
        model = self.db.query(UserModel).filter_by(email=email).first()
        return self._to_entity(model) if model else None

    def create(self, user: User) -> User:
        model = UserModel(
            username=user.username,
            email=user.email,
            password_hash=user.password_hash,
            is_email_verified=user.is_email_verified
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def change_email(self, user: User, new_email: str) -> User:
        model = self.db.get(UserModel, user.id)
        if not model:
            raise ValueError("User not found")

        model.email = new_email
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def change_username(self, user: User, new_username: str) -> User:
        model = self.db.get(UserModel, user.id)
        if not model:
            raise ValueError("User not found")

        model.username = new_username
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def change_password(self, user: User, new_password_hash: str) -> User:
        model = self.db.get(UserModel, user.id)
        if not model:
            raise ValueError("User not found")

        model.password_hash = new_password_hash
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def delete(self, user: User) -> None:
        model = self.db.get(UserModel, user.id)
        if not model:
            raise ValueError("User not found")

        self.db.delete(model)
        self.db.commit()

    def mark_email_as_verified(self, user_id: int):
        model = self.db.get(UserModel, user_id)
        if not model:
            raise ValueError("User not found")

        model.is_email_verified = True
        self.db.commit()
        self.db.refresh(model)
