from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID, uuid4
import httpx

from reforma_survey.presentation.dependencies import get_current_user_id, get_db
from reforma_survey.infrastructure.repositories.user_profile_repository_impl import UserProfileRepositoryImpl
from reforma_survey.presentation.schemas.balance_schema import TopUpRequest

router = APIRouter(prefix="/balance", tags=["Balance"])


@router.post("/topup")
async def topup_balance(
    request: TopUpRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    db = Depends(get_db)
):
    idempotency_key = request.idempotency_key or str(uuid4())

    try:
        # Синхронный вызов к reforma-payment
        resp = httpx.post(
            "http://reforma-payment:8000/payments/topup/initiate",
            json={
                "user_id": str(current_user_id),
                "amount": request.amount,
                "currency": "RUB",
                "idempotency_key": idempotency_key,
                "description": "Пополнение баланса",
                "metadata": {"source": "survey-service"}
            },
            headers={"Authorization": "Bearer internal-payment-token"},
            timeout=8.0
        )

        if resp.status_code != 200:
            raise HTTPException(resp.status_code, resp.json().get("detail", "Ошибка платежа"))

        data = resp.json()

        return {
            "payment_id": data["payment_id"],
            "status": data["status"],
            "redirect_url": data.get("redirect_url"),
            "client_secret": data.get("client_secret")
        }

    except httpx.TimeoutException:
        raise HTTPException(504, "Платёжный сервис не отвечает")
    except Exception as e:
        raise HTTPException(500, "Внутренняя ошибка")