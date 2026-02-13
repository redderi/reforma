from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from reforma_authorization.domain.entities.user import User
from reforma_authorization.presentation.dependencies.current_user import get_current_user_id
from reforma_authorization.presentation.dependencies.get_db import get_db
from reforma_authorization.infrastructure.repositories.email_verification_token_impl import EmailTokenRepositoryImpl
from reforma_authorization.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from reforma_authorization.infrastructure.repositories.refresh_token_repository_impl import RefreshTokenRepositoryImpl
from reforma_authorization.infrastructure.security.password_hasher import BcryptPasswordHasher
from reforma_authorization.infrastructure.security.jwt_service import JWTService
from reforma_authorization.application.auth.login_use_case import LoginUseCase
from reforma_authorization.application.auth.refresh_use_case import RefreshAccessTokenUseCase
from reforma_authorization.application.auth.logout_use_case import LogoutUseCase
from reforma_authorization.application.auth.register_use_case import RegisterUseCase
from reforma_authorization.presentation.schemas.auth_request import RegisterRequest, LoginRequest
from reforma_authorization.infrastructure.rabbitmq.publisher import EventPublisher
from reforma_authorization.common.logger import log_info, log_warning, log_error
from uuid import UUID

event_publisher = EventPublisher()
router = APIRouter(prefix="/auth", tags=["Auth"])


# ----------------- Current User -----------------
@router.get("/me")
async def me(
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    user_repo = UserRepositoryImpl(db)
    user = await user_repo.get_by_id(current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "is_email_verified": user.is_email_verified,
    }


# ----------------- Refresh Token Helpers -----------------
def get_refresh_token(request: Request) -> str:
    refresh_token = request.cookies.get("refresh_token") or request.headers.get("X-Refresh-Token")
    if not refresh_token:
        log_warning("Refresh token not provided", service="auth-service")
        raise HTTPException(status_code=401, detail="Refresh token not provided")
    return refresh_token


def set_refresh_cookie(response: Response, refresh_token: str):
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        samesite="lax"
    )


# ----------------- Register -----------------
@router.post("/register")
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    log_info(f"Register attempt for username={data.username}, email={data.email}", service="auth-service")
    try:
        use_case = RegisterUseCase(
            user_repo=UserRepositoryImpl(db),
            token_repo=EmailTokenRepositoryImpl(db),
            password_hasher=BcryptPasswordHasher(),
            event_publisher=event_publisher
        )
        await use_case.execute(username=data.username, email=data.email, password=data.password)
        log_info(f"User registered successfully: {data.username}", service="auth-service")
        return {"message": "Регистрация прошла успешно. Подтвердите email, чтобы завершить регистрацию."}
    except ValueError as e:
        log_warning(f"Registration failed: {e}", service="auth-service", context={"username": data.username, "email": data.email})
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Unexpected error during registration: {e}", service="auth-service")
        raise HTTPException(status_code=500, detail="Internal server error")


# ----------------- Login -----------------
@router.post("/login")
async def login(data: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    log_info(f"Login attempt for email={data.email}", service="auth-service", context={"device_id": data.device_id})
    try:
        use_case = LoginUseCase(
            user_repo=UserRepositoryImpl(db),
            refresh_repo=RefreshTokenRepositoryImpl(db),
            password_hasher=BcryptPasswordHasher(),
            token_service=JWTService()
        )
        result = await use_case.execute(data.email, data.password, data.device_id)

        response.set_cookie(
            key="refresh_token",
            value=result["refresh_token"],
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=60 * 60 * 24 * 30
        )

        log_info(f"User logged in successfully: {data.email}", service="auth-service")
        return {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": "bearer"
        }
    except ValueError:
        log_warning(f"Login failed for email={data.email}", service="auth-service")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        log_error(f"Unexpected error during login: {e}", service="auth-service")
        raise HTTPException(status_code=500, detail="Internal server error")


# ----------------- Refresh -----------------
@router.post("/refresh")
async def refresh(response: Response, refresh_token: str = Depends(get_refresh_token), db: AsyncSession = Depends(get_db)):
    log_info("Refresh token attempt", service="auth-service")
    try:
        use_case = RefreshAccessTokenUseCase(
            refresh_repo=RefreshTokenRepositoryImpl(db),
            token_service=JWTService()
        )
        result = await use_case.execute(refresh_token)

        access_token = result["access_token"]
        new_refresh_token = result["refresh_token"]

        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            max_age=60 * 60 * 24 * 7,
            samesite="lax"
        )

        log_info("Access token refreshed successfully", service="auth-service")
        return {"access_token": access_token}
    except ValueError:
        log_warning("Invalid refresh token", service="auth-service")
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    except Exception as e:
        log_error(f"Unexpected error during token refresh: {e}", service="auth-service")
        raise HTTPException(status_code=500, detail="Internal server error")


# ----------------- Logout -----------------
@router.post("/logout")
async def logout(refresh_token: str = Depends(get_refresh_token), db: AsyncSession = Depends(get_db)):
    log_info("Logout attempt", service="auth-service")
    refresh_repo = RefreshTokenRepositoryImpl(db)
    use_case = LogoutUseCase(refresh_repo)
    try:
        await use_case.execute(refresh_token)
        log_info("User logged out successfully", service="auth-service")
        return {"detail": "Logged out"}
    except ValueError as ve:
        log_error(f"Logout failed: {ve}", service="auth-service")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        log_error(f"Unexpected error during logout: {e}", service="auth-service")
        raise HTTPException(status_code=500, detail="Internal server error")


# ----------------- Verify Email -----------------
@router.get("/verify_email")
async def verify_email(token: str = Query(...), db: AsyncSession = Depends(get_db)):
    log_info(f"Email verification attempt for token={token}", service="auth-service")
    try:
        token_repo = EmailTokenRepositoryImpl(db)
        user_repo = UserRepositoryImpl(db)

        token_obj = await token_repo.get(token)
        if not token_obj:
            log_warning(f"Invalid or expired email verification token: {token}", service="auth-service")
            raise HTTPException(status_code=400, detail="Неверный или просроченный токен")

        await user_repo.mark_email_as_verified(token_obj.user_id)

        user = await user_repo.get_by_id(token_obj.user_id)
        log_info(f"user_id={user.id}, is_email_verified={user.is_email_verified}", service="auth-service")

        await token_repo.delete(token_obj.token)

        log_info(f"Email verified successfully for user_id={token_obj.user_id}", service="auth-service")
        return {"message": "Email успешно подтверждён"}
    except Exception as e:
        log_error(f"Unexpected error during email verification: {e}", service="auth-service")
        raise HTTPException(status_code=500, detail=str(e))
