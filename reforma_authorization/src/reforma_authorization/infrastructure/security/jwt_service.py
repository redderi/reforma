from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from uuid import UUID, uuid4
from reforma_authorization.domain.services.token_service import TokenService
from reforma_authorization.infrastructure.config.jwt_config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class JWTService(TokenService):
    def create_access_token(
        self, user_id: UUID, user_role: str, user_status: str
    ) -> str:
        payload = {
            "sub": str(user_id),
            "role": user_role,
            "status": user_status,
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            "iat": datetime.utcnow(),
            "iss": "reforma-api",
            "type": "access",
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    def create_refresh_token(
        self, user_id: UUID, device_id: str | None = None
    ) -> str:
        payload = {
            "sub": str(user_id),
            "device_id": device_id,
            "exp": datetime.utcnow() + timedelta(days=7),
            "iat": datetime.utcnow(),
            "iss": "reforma-api",
            "type": "refresh",
            "jti": str(uuid4()),
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    def decode_token(self, token: str) -> dict | None:
        try:
            return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        except JWTError:
            return None
