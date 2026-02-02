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
from main import mail_publisher

router = APIRouter(prefix="/auth", tags=["Auth"])

def get_refresh_token(request: Request) -> str:
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        refresh_token = request.headers.get("X-Refresh-Token")
    if not refresh_token:
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
async def register(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    try:
        use_case = RegisterUseCase(
            user_repo=UserRepositoryImpl(db),
            token_repo=EmailTokenRepositoryImpl(db),
            password_hasher=BcryptPasswordHasher(),
            mail_producer=mail_publisher
        )
        await use_case.execute(
            username=data.username,
            email=data.email,
            password=data.password
        )
        return {"message": "Регистрация прошла успешно. Подтвердите email, чтобы завершить регистрацию."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(
    data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    try:
        result = LoginUseCase(
            UserRepositoryImpl(db),
            RefreshTokenRepositoryImpl(db),
            BcryptPasswordHasher(),
            JWTService()
        ).execute(
            data.email,
            data.password,
            data.device_id
        )
        response.set_cookie(
            key="refresh_token",
            value=result["refresh_token"],
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=60 * 60 * 24 * 30
        )
        return {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": "bearer"
        }
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/refresh")
async def refresh(
    response: Response,
    refresh_token: str = Depends(get_refresh_token),
    db: Session = Depends(get_db)
):
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
        return {"access_token": access_token}
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.post("/logout")
async def logout(
    refresh_token: str = Depends(get_refresh_token),
    db: Session = Depends(get_db)
):
    LogoutUseCase(
        RefreshTokenRepositoryImpl(db)
    ).execute(refresh_token)
    return {"detail": "Logged out"}

@router.get("/verify_email")
async def verify_email(
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    token_repo = EmailTokenRepositoryImpl(db)
    user_repo = UserRepositoryImpl(db)
    user_id = token_repo.get_valid_user_id_by_token(token)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user_repo.mark_email_as_verified(user_id)
    token_repo.delete_token(token)
    return {"message": "Email успешно подтверждён"}
