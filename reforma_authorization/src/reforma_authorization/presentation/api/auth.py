from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from reforma_authorization.application.admin.deactivate_user_use_case import DeactivateUserUseCase
from reforma_authorization.application.auth.restore_user_use_case import RestoreUserUseCase
from reforma_authorization.application.user.soft_delete_use_case import SoftDeleteUserUseCase
from reforma_authorization.application.auth.verify_email_use_case import VerifyEmailUseCase
from reforma_authorization.application.auth.verify_restore_use_case import VerifyRestoreUseCase
from reforma_authorization.application.auth.verify_password_change import VerifyPasswordChangeUseCase
from reforma_common.user_status import UserStatus
from sqlalchemy.ext.asyncio import AsyncSession
from reforma_authorization.domain.entities.user import User
from reforma_authorization.presentation.dependencies.get_current_user_id import get_current_user_id
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
from reforma_authorization.presentation.schemas.auth_request import RegisterRequest, LoginRequest, RestoreRequest
from reforma_authorization.infrastructure.rabbitmq.publisher import EventPublisher
from reforma_common.logger import log_info, log_warning, log_error
from uuid import UUID

event_publisher = EventPublisher()
router = APIRouter(prefix="/auth", tags=["Auth"])


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

        user = await UserRepositoryImpl(db).get_by_email(data.email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.status in [UserStatus.DEACTIVATED, UserStatus.SUSPENDED, UserStatus.DELETED]:
            log_warning(f"Blocked login for user_id={user.id} due to status={user.status}", service="auth-service")
            raise HTTPException(status_code=403, detail=f"User account is {user.status}")

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
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Unexpected error during login: {e}", service="auth-service")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/refresh")
async def refresh(response: Response, refresh_token: str = Depends(get_refresh_token), db: AsyncSession = Depends(get_db)):
    log_info("Refresh token attempt", service="auth-service")
    try:
        use_case = RefreshAccessTokenUseCase(
            refresh_repo=RefreshTokenRepositoryImpl(db),
            token_service=JWTService()
        )
        result = await use_case.execute(refresh_token)

        user_repo = UserRepositoryImpl(db)
        user = await user_repo.get_by_id(result["user_id"])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.status in [UserStatus.DEACTIVATED, UserStatus.SUSPENDED, UserStatus.DELETED]:
            log_warning(f"Blocked refresh for user_id={user.id} due to status={user.status}", service="auth-service")
            raise HTTPException(status_code=403, detail=f"User account is {user.status}")

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
    except HTTPException:
        raise
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


@router.get("/verify_email")
async def verify_email(token: str = Query(...), db: AsyncSession = Depends(get_db)):
    try:
        use_case = VerifyEmailUseCase(UserRepositoryImpl(db), EmailTokenRepositoryImpl(db))
        return await use_case.execute(token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Unexpected error during email verification: {e}", service="auth-service")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/verify_restore")
async def verify_restore(token: str = Query(...), db: AsyncSession = Depends(get_db)):
    try:
        use_case = VerifyRestoreUseCase(UserRepositoryImpl(db), EmailTokenRepositoryImpl(db))
        return await use_case.execute(token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Unexpected error during restore verification: {e}", service="auth-service")
        raise HTTPException(status_code=500, detail=str(e))

    

@router.delete("/soft-delete")
async def delete_user(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Delete user attempt for user_id={user_id}", service="auth-service")

    try:
        use_case = SoftDeleteUserUseCase(
            UserRepositoryImpl(db),
        )
        await use_case.execute(user_id)
        log_info(f"User deleted successfully: user_id={user_id}", service="auth-service")
        return {"detail": "User deleted successfully."}

    except ValueError as e:
        log_warning(f"Failed to delete user user_id={user_id}: {e}", service="auth-service")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        log_error(f"Unexpected error deleting user user_id={user_id}: {e}", service="auth-service")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@router.get("/verify_password_change")
async def confirm_password_change(token: str = Query(...), db: AsyncSession = Depends(get_db)):
    try:
        use_case = VerifyPasswordChangeUseCase(
            UserRepositoryImpl(db),
            EmailTokenRepositoryImpl(db),
            RefreshTokenRepositoryImpl(db)
        )
        return await use_case.execute(token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Unexpected error during password verification: {e}", service="auth-service")
        raise HTTPException(status_code=500, detail=str(e))

    
@router.post("/deactivate")
async def deactivate_me(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    try:
        log_info(f"Deactivating user {user_id}", service="auth-service")
        use_case = DeactivateUserUseCase(UserRepositoryImpl(db))
        user = await use_case.execute(user_id)
        log_info(f"User {user_id} deactivated successfully", service="auth-service")
        return user.__dict__
    except Exception as e:
        log_error(f"Unexpected error during user deactivation: {e}", service="auth-service", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/restore")
async def restore_me(
    data: RestoreRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        log_info(f"Restore request for email: {data.email}", service="auth-service")
        repo = UserRepositoryImpl(db)
        token_repo = EmailTokenRepositoryImpl(db)
        user = await repo.get_by_email(data.email)

        if not user:
            log_error(f"User not found for email: {data.email}", service="auth-service")
            raise HTTPException(status_code=404, detail="User not found")

        if user.status != UserStatus.DEACTIVATED:
            log_error(f"User {user.id} cannot be restored, status: {user.status}", service="auth-service")
            raise HTTPException(status_code=400, detail="User cannot be restored")

        use_case = RestoreUserUseCase(user_repo=repo, token_repo=token_repo, event_publisher=event_publisher)
        await use_case.execute(user_id=user.id)

        log_info(f"Restore email sent for user {user.id}", service="auth-service")
        return {"message": "Письмо для восстановления аккаунта отправлено на вашу почту"}

    except Exception as e:
        log_error(f"Unexpected error during user restoration: {e}", service="auth-service", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")