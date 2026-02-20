from fastapi import Depends, HTTPException
from reforma_survey.infrastructure.security.jwt_service import (
    decode_token,
    oauth2_scheme,
)


def get_current_user_role(token: str = Depends(oauth2_scheme)) -> str:
    payload = decode_token(token)
    if not payload or "role" not in payload:
        raise HTTPException(status_code=401, detail="Invalid access token for role")
    return str(payload["role"])
