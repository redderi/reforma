from fastapi import Depends
from reforma_survey.infrastructure.security.jwt_service import (
    decode_token,
    oauth2_scheme,
)
from uuid import UUID


def get_optional_user_id(token: str | None = Depends(oauth2_scheme)) -> UUID | None:

    if token is None:
        return None
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        return None
    try:
        return UUID(payload["sub"])
    except ValueError:
        return None
