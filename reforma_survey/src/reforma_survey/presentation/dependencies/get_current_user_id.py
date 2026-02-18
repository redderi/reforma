from fastapi import Depends, HTTPException
from reforma_survey.infrastructure.security.jwt_service import decode_access_token, oauth2_scheme
import uuid

def get_current_user_id(token: str = Depends(oauth2_scheme)) -> uuid.UUID:
    payload = decode_access_token(token)

    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid access token")

    return uuid.UUID(payload["sub"])
