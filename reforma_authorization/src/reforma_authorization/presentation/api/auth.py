from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session
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
from reforma_authorization.infrastructure.rabbitmq.publisher import MailPublisher
from reforma_authorization.common.logger import log_info, log_warning, log_error 

mail_publisher = MailPublisher()

router = APIRouter(prefix="/auth", tags=["Auth"])

def get_refresh_token(request: Request) -> str:
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        refresh_token = request.headers.get("X-Refresh-Token")
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

@router.post("/register")
async def register(data: RegisterRequest, db: Session = Depends(get_db)):
    log_info(f"Register attempt for username={data.username}, email={data.email}", service="auth-service")
    try:
        use_case = RegisterUseCase(
            user_repo=UserRepositoryImpl(db),
            token_repo=EmailTokenRepositoryImpl(db),
            password_hasher=BcryptPasswordHasher(),
            mail_publisher=mail_publisher
        )
        await use_case.execute(
            username=data.username,
            email=data.email,
            password=data.password
        )
        log_info(f"User registered successfully: {data.username}", service="auth-service")
        return {"message": "Регистрация прошла успешно. Подтвердите email, чтобы завершить регистрацию."}
    except ValueError as e:
        log_warning(f"Registration failed: {e}", service="auth-service", context={"username": data.username, "email": data.email})
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Unexpected error during registration: {e}", service="auth-service")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/login")
async def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    log_info(f"Login attempt for email={data.email}", service="auth-service", context={"device_id": data.device_id})
    try:
        log_info(f"data.email = {data.email}, data.password = {data.password}, data.device_id = {data.device_id}", service="auth-service")
        result = LoginUseCase(
            UserRepositoryImpl(db),
            RefreshTokenRepositoryImpl(db),
            BcryptPasswordHasher(),
            JWTService()
        ).execute(data.email, data.password, data.device_id)

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

@router.post("/refresh")
async def refresh(response: Response, refresh_token: str = Depends(get_refresh_token), db: Session = Depends(get_db)):
    log_info("Refresh token attempt", service="auth-service")
    try:
        result = RefreshAccessTokenUseCase(
            RefreshTokenRepositoryImpl(db),
            JWTService()
        ).execute(refresh_token)

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

@router.post("/logout")
async def logout(refresh_token: str = Depends(get_refresh_token), db: Session = Depends(get_db)):
    log_info("Logout attempt", service="auth-service")
    try:
        LogoutUseCase(
            RefreshTokenRepositoryImpl(db)
        ).execute(refresh_token)
        log_info("User logged out successfully", service="auth-service")
        return {"detail": "Logged out"}
    except Exception as e:
        log_error(f"Unexpected error during logout: {e}", service="auth-service")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/verify_email")
async def verify_email(token: str = Query(...), db: Session = Depends(get_db)):
    log_info(f"Email verification attempt for token={token}", service="auth-service")
    try:
        token_repo = EmailTokenRepositoryImpl(db)
        user_repo = UserRepositoryImpl(db)

        token_obj = token_repo.get(token)
        if not token_obj:
            log_warning(f"Invalid or expired email verification token: {token}", service="auth-service")
            raise HTTPException(status_code=400, detail="Неверный или просроченный токен")

        user_repo.mark_email_as_verified(token_obj.user_id)
        #
        #
        #
        user = user_repo.get_by_id(token_obj.user_id)
        log_info(f"user_id ={user.id}, is_email_verify = {user.is_email_verified} ", service="auth-service")
        token_repo.delete(token_obj.token)

        log_info(f"Email verified successfully for user_id={token_obj.user_id}", service="auth-service")
        return {"message": "Email успешно подтверждён"}
    except Exception as e:
        log_error(f"Unexpected error during email verification: {e}", service="auth-service")
        raise HTTPException(status_code=500, detail=str(e))