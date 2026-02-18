from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer

from reforma_payment.infrastructure.config.jwt_config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
