from fastapi import HTTPException, Header
from reforma_survey.infrastructure.config.api_config import INTERNAL_API_KEY


async def verify_api_key(x_api_key: str | None = Header(None)):
    if x_api_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden: invalid API key")
