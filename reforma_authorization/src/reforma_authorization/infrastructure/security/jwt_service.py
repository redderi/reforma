from datetime import datetime, timedelta
from jose import jwt, JWTError
import secrets
from fastapi.security import OAuth2PasswordBearer
import uuid

from reforma_authorization.domain.services.token_service import TokenService
from reforma_authorization.infrastructure.config.jwt_config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class JWTService(TokenService):

    def create_access_token(self, user_id: uuid.UUID) -> str:
        payload = {
            "sub": str(user_id),
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            "iat": datetime.utcnow(),
            "iss": "reforma-api",
        }

        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    def create_refresh_token(self) -> str:
        return secrets.token_urlsafe(64)

    def decode_access_token(self, token: str) -> dict | None:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except JWTError:
            return None
