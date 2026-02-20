from fastapi import Depends, HTTPException
from reforma_authorization.infrastructure.security.jwt_service import (
    JWTService,
    oauth2_scheme,
)
from uuid import UUID


def get_current_user_id(token: str = Depends(oauth2_scheme)) -> UUID:
    payload = JWTService().decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid access token")
    return UUID(payload["sub"])
