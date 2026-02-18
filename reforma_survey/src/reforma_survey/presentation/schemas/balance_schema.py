from pydantic import BaseModel


class TopUpRequest(BaseModel):
    amount: int 
    idempotency_key: str | None = None