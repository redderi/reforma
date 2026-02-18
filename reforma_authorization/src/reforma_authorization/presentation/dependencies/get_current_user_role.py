from fastapi import Depends, HTTPException
from reforma_authorization.infrastructure.security.jwt_service import JWTService, oauth2_scheme

def get_current_user_role(token: str = Depends(oauth2_scheme)) -> str:
    payload = JWTService().decode_access_token(token)

    if not payload or "role" not in payload:
        raise HTTPException(status_code=401, detail="Invalid access token for role")

    return str(payload["role"])
