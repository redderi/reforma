from passlib.context import CryptContext
from reforma_authorization.domain.services.password_hasher import PasswordHasher

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

class BcryptPasswordHasher(PasswordHasher):
    
    def hash(self, plain: str) -> str:
        return pwd.hash(plain)

    def verify(self, plain: str, hashed: str) -> bool:
        return pwd.verify(plain,hashed)