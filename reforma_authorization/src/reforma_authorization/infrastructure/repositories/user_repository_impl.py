from reforma_authorization.domain.repositories.user_repository import UserRepository
from reforma_authorization.domain.entities.user import User
from reforma_authorization.infrastructure.db.models import UserModel
from sqlalchemy.orm import Session

class UserRepositoryImpl(UserRepository):

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: int) -> User | None:
        model = self.db.query(UserModel).filter_by(id=id).first()
        if not model:
            return None
        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            password_hash=model.password_hash
        )
    
    def get_by_username(self, username: str) -> User | None:
        model = self.db.query(UserModel).filter_by(username=username).first()
        if not model:
            return None
        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            password_hash=model.password_hash
        )

    def get_by_email(self, email: str) -> User | None:
        model = self.db.query(UserModel).filter_by(email=email).first()
        if not model:
            return None
        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            password_hash=model.password_hash
        )

    def create(self, user: User) -> User:
        model = UserModel(
            username=user.username,
            email=user.email,
            password_hash=user.password_hash
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)

        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            password_hash=model.password_hash
        )
    
    def change_email(self, user: User, new_email: str) -> User:
        model = self.db.query(UserModel).get(user.id)
        if not model:
            raise ValueError("User not found")
        
        model.email = new_email
        self.db.commit()
        self.db.refresh(model)

        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            password_hash=model.password_hash
        )

    def change_username(self, user: User, new_username: str) -> User:
        model = self.db.query(UserModel).get(user.id)
        if not model:
            raise ValueError("User not found")
        
        model.username = new_username
        self.db.commit()
        self.db.refresh(model)

        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            password_hash=model.password_hash
        )

    def change_password(self, user: User, new_password_hash: str) -> User:
        model = self.db.query(UserModel).get(user.id)
        if not model:
            raise ValueError("User not found")
        
        model.password_hash = new_password_hash
        self.db.commit()
        self.db.refresh(model)

        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            password_hash=model.password_hash
        )

    def delete(self, user: User) -> None:
        model = self.db.query(UserModel).get(user.id)
        if not model:
            raise ValueError("User not found")
        
        self.db.delete(model)
        self.db.commit()

    def mark_email_as_verified(self, user_id: int):
        self.db.query(UserModel)\
            .filter_by(id=user_id)\
            .update({"is_email_verified": True})
        self.db.commit()
