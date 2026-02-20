from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from reforma_authorization.application.admin.deactivate_user_use_case import (
    DeactivateUserUseCase,
)
from reforma_authorization.application.auth.restore_user_use_case import (
    RestoreUserUseCase,
)
from reforma_authorization.application.user.soft_delete_use_case import (
    SoftDeleteUserUseCase,
)
from reforma_authorization.application.auth.verify_email_use_case import (
    VerifyEmailUseCase,
)
from reforma_authorization.application.auth.verify_restore_use_case import (
    VerifyRestoreUseCase,
)
from reforma_authorization.application.auth.verify_password_change import (
    VerifyPasswordChangeUseCase,
)
from reforma_authorization.infrastructure.rabbitmq.publisher import EventPublisher
from reforma_authorization.presentation.dependencies.get_event_publisher import (
    get_event_publisher,
)
from reforma_common.user_status import UserStatus
from sqlalchemy.ext.asyncio import AsyncSession
from reforma_authorization.presentation.dependencies.get_current_user_id import (
    get_current_user_id,
)
from reforma_authorization.presentation.dependencies.get_db import get_db
from reforma_authorization.infrastructure.repositories.email_verification_token_impl import (
    EmailTokenRepositoryImpl,
)
from reforma_authorization.infrastructure.repositories.user_repository_impl import (
    UserRepositoryImpl,
)
from reforma_authorization.infrastructure.repositories.refresh_token_repository_impl import (
    RefreshTokenRepositoryImpl,
)
from reforma_authorization.infrastructure.security.password_hasher import (
    BcryptPasswordHasher,
)
from reforma_authorization.infrastructure.security.jwt_service import JWTService
from reforma_authorization.application.auth.login_use_case import LoginUseCase
from reforma_authorization.application.auth.refresh_use_case import (
    RefreshAccessTokenUseCase,
)
from reforma_authorization.application.auth.logout_use_case import LogoutUseCase
from reforma_authorization.application.auth.register_use_case import RegisterUseCase
from reforma_authorization.presentation.schemas.auth_request import (
    RegisterRequest,
    LoginRequest,
    RestoreRequest,
)
from reforma_common.logger import log_info, log_warning, log_error
from uuid import UUID

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/me")
async def me(
    request: Request,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Request current user information",
        service="auth-service",
        request=request,
        user_id=current_user_id,
        trace_id=trace_id,
    )

    user_repo = UserRepositoryImpl(db)
    user = await user_repo.get_by_id(current_user_id)
    if not user:
        log_warning(
            "User not found when requesting /me",
            service="auth-service",
            request=request,
            user_id=current_user_id,
            trace_id=trace_id,
        )
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "is_email_verified": user.is_email_verified,
    }


def get_refresh_token(request: Request) -> str:
    trace_id = getattr(request.state, "trace_id", None)
    refresh_token = request.cookies.get("refresh_token") or request.headers.get(
        "X-Refresh-Token"
    )

    if not refresh_token:
        log_warning(
            "Refresh token not provided",
            service="auth-service",
            request=request,
            trace_id=trace_id,
        )
        raise HTTPException(status_code=401, detail="Refresh token not provided")

    return refresh_token


def set_refresh_cookie(response: Response, refresh_token: str):
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        samesite="lax",
    )


@router.post("/register")
async def register(
    data: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    event_publisher: EventPublisher = Depends(get_event_publisher),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Registration attempt",
        service="auth-service",
        request=request,
        trace_id=trace_id,
        context={"username": data.username, "email": data.email},
    )

    try:
        use_case = RegisterUseCase(
            user_repo=UserRepositoryImpl(db),
            token_repo=EmailTokenRepositoryImpl(db),
            password_hasher=BcryptPasswordHasher(),
            event_publisher=event_publisher,
        )
        await use_case.execute(
            username=data.username, email=data.email, password=data.password
        )

        log_info(
            "User registered successfully",
            service="auth-service",
            request=request,
            trace_id=trace_id,
            context={"username": data.username, "email": data.email},
        )
        return {
            "message": "Registration successful. Please verify your email to complete."
        }

    except ValueError as e:
        log_warning(
            f"Registration failed: {str(e)}",
            service="auth-service",
            request=request,
            trace_id=trace_id,
            context={
                "username": data.username,
                "email": data.email,
                "error_detail": str(e),
            },
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            f"Unexpected error during registration: {str(e)}",
            service="auth-service",
            request=request,
            trace_id=trace_id,
            context={"username": data.username, "email": data.email},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/login")
async def login(
    data: LoginRequest,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Login attempt",
        service="auth-service",
        request=request,
        trace_id=trace_id,
        context={"email": data.email, "device_id": data.device_id},
    )

    try:
        use_case = LoginUseCase(
            user_repo=UserRepositoryImpl(db),
            refresh_repo=RefreshTokenRepositoryImpl(db),
            password_hasher=BcryptPasswordHasher(),
            token_service=JWTService(),
        )
        result = await use_case.execute(data.email, data.password, data.device_id)

        user = await UserRepositoryImpl(db).get_by_email(data.email)
        if not user:
            log_warning(
                "User not found during login attempt",
                service="auth-service",
                request=request,
                trace_id=trace_id,
                context={"email": data.email},
            )
            raise HTTPException(status_code=404, detail="User not found")

        if user.status in [
            UserStatus.DEACTIVATED,
            UserStatus.SUSPENDED,
            UserStatus.DELETED,
        ]:
            log_warning(
                "Login blocked due to account status",
                service="auth-service",
                request=request,
                user_id=user.id,
                trace_id=trace_id,
                context={"email": data.email, "user_status": user.status.value},
            )
            raise HTTPException(
                status_code=403, detail=f"User account is {user.status}"
            )

        set_refresh_cookie(response, result["refresh_token"])

        log_info(
            "User logged in successfully",
            service="auth-service",
            request=request,
            user_id=user.id,
            trace_id=trace_id,
            context={"email": data.email, "device_id": data.device_id},
        )
        return {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": "bearer",
        }

    except ValueError:
        log_warning(
            "Login failed: invalid credentials",
            service="auth-service",
            request=request,
            trace_id=trace_id,
            context={"email": data.email, "device_id": data.device_id},
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    except Exception as e:
        log_error(
            f"Unexpected error during login: {str(e)}",
            service="auth-service",
            request=request,
            trace_id=trace_id,
            context={"email": data.email},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/refresh")
async def refresh(
    response: Response,
    request: Request,
    refresh_token: str = Depends(get_refresh_token),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Refresh token attempt",
        service="auth-service",
        request=request,
        trace_id=trace_id,
    )

    try:
        use_case = RefreshAccessTokenUseCase(
            refresh_repo=RefreshTokenRepositoryImpl(db), token_service=JWTService()
        )
        result = await use_case.execute(refresh_token)

        access_token = result["access_token"]
        new_refresh_token = result["refresh_token"]

        set_refresh_cookie(response, new_refresh_token)

        log_info(
            "Token refreshed successfully",
            service="auth-service",
            request=request,
            trace_id=trace_id,
        )
        return {"access_token": access_token}

    except ValueError as ve:
        context = {"error_detail": str(ve)}
        if "отозван" in str(ve).lower() or "revoked" in str(ve).lower():
            log_warning(
                "Attempt to use revoked refresh token",
                service="auth-service",
                request=request,
                trace_id=trace_id,
                context=context,
            )
            raise HTTPException(status_code=403, detail="Token revoked")

        if "истёк" in str(ve).lower() or "expired" in str(ve).lower():
            log_warning(
                "Attempt to use expired refresh token",
                service="auth-service",
                request=request,
                trace_id=trace_id,
                context=context,
            )
            raise HTTPException(status_code=401, detail="Refresh token expired")

        log_warning(
            "Invalid refresh token",
            service="auth-service",
            request=request,
            trace_id=trace_id,
            context=context,
        )
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    except Exception as e:
        log_error(
            f"Unexpected error during token refresh: {str(e)}",
            service="auth-service",
            request=request,
            trace_id=trace_id,
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/logout")
async def logout(
    request: Request,
    refresh_token: str = Depends(get_refresh_token),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Logout attempt", service="auth-service", request=request, trace_id=trace_id
    )

    refresh_repo = RefreshTokenRepositoryImpl(db)
    use_case = LogoutUseCase(refresh_repo)
    try:
        success = await use_case.execute(refresh_token)
        log_info(
            "User logged out successfully",
            service="auth-service",
            request=request,
            trace_id=trace_id,
        )
        if success:
            return {"detail": "Logged out"}
        else:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

    except ValueError as ve:
        log_error(
            f"Logout failed: {str(ve)}",
            service="auth-service",
            request=request,
            trace_id=trace_id,
            context={"error_detail": str(ve)},
        )
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        log_error(
            f"Unexpected error during logout: {str(e)}",
            service="auth-service",
            request=request,
            trace_id=trace_id,
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/verify_email")
async def verify_email(
    request: Request, token: str = Query(...), db: AsyncSession = Depends(get_db)
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Email verification attempt",
        service="auth-service",
        request=request,
        trace_id=trace_id,
        context={"token_prefix": token[:10] + "..." if token else "missing"},
    )

    try:
        use_case = VerifyEmailUseCase(
            UserRepositoryImpl(db), EmailTokenRepositoryImpl(db)
        )
        await use_case.execute(token)
        log_info(
            "Email successfully verified",
            service="auth-service",
            request=request,
            trace_id=trace_id,
            context={"token_prefix": token[:10] + "..."},
        )
        return {"message": "Email successfully confirmed"}

    except ValueError as e:
        log_warning(
            f"Email verification failed: {str(e)}",
            service="auth-service",
            request=request,
            trace_id=trace_id,
            context={
                "token_prefix": token[:10] + "..." if token else "missing",
                "error_detail": str(e),
            },
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            f"Unexpected error during email verification: {str(e)}",
            service="auth-service",
            request=request,
            trace_id=trace_id,
            context={"token_prefix": token[:10] + "..." if token else "missing"},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/verify_restore")
async def verify_restore(
    request: Request, token: str = Query(...), db: AsyncSession = Depends(get_db)
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Restore verification attempt",
        service="auth-service",
        request=request,
        trace_id=trace_id,
        context={"token_prefix": token[:10] + "..." if token else "missing"},
    )

    try:
        use_case = VerifyRestoreUseCase(
            UserRepositoryImpl(db), EmailTokenRepositoryImpl(db)
        )
        await use_case.execute(token)
        log_info(
            "Restore token successfully verified",
            service="auth-service",
            request=request,
            trace_id=trace_id,
            context={"token_prefix": token[:10] + "..."},
        )
        return {"message": "The account has been successfully restored and activated."}

    except ValueError as e:
        log_warning(
            f"Restore verification failed: {str(e)}",
            service="auth-service",
            request=request,
            trace_id=trace_id,
            context={
                "token_prefix": token[:10] + "..." if token else "missing",
                "error_detail": str(e),
            },
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            f"Unexpected error during restore verification: {str(e)}",
            service="auth-service",
            request=request,
            trace_id=trace_id,
            context={"token_prefix": token[:10] + "..." if token else "missing"},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/soft-delete")
async def delete_user(
    request: Request,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Soft-delete account attempt",
        service="auth-service",
        request=request,
        user_id=user_id,
        trace_id=trace_id,
    )

    try:
        use_case = SoftDeleteUserUseCase(UserRepositoryImpl(db))
        await use_case.execute(user_id)
        log_info(
            "Account successfully soft-deleted",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id,
        )
        return {"detail": "User deleted successfully."}

    except ValueError as e:
        log_warning(
            "Failed to soft-delete user",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id,
            context={"error_detail": str(e)},
        )
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        log_error(
            f"Unexpected error during soft-delete: {str(e)}",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id,
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/verify_password_change")
async def confirm_password_change(
    request: Request, token: str = Query(...), db: AsyncSession = Depends(get_db)
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Password change verification attempt",
        service="auth-service",
        request=request,
        trace_id=trace_id,
        context={"token_prefix": token[:10] + "..." if token else "missing"},
    )

    try:
        use_case = VerifyPasswordChangeUseCase(
            UserRepositoryImpl(db),
            EmailTokenRepositoryImpl(db),
            RefreshTokenRepositoryImpl(db),
        )
        await use_case.execute(token)
        log_info(
            "Password change token successfully verified",
            service="auth-service",
            request=request,
            trace_id=trace_id,
            context={"token_prefix": token[:10] + "..."},
        )
        return {"message": "Password changed successfully"}

    except ValueError as e:
        log_warning(
            f"Password change verification failed: {str(e)}",
            service="auth-service",
            request=request,
            trace_id=trace_id,
            context={
                "token_prefix": token[:10] + "..." if token else "missing",
                "error_detail": str(e),
            },
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            f"Unexpected error during password change verification: {str(e)}",
            service="auth-service",
            request=request,
            trace_id=trace_id,
            context={"token_prefix": token[:10] + "..." if token else "missing"},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/deactivate")
async def deactivate_me(
    request: Request,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Account deactivation attempt",
        service="auth-service",
        request=request,
        user_id=user_id,
        trace_id=trace_id,
    )

    try:
        use_case = DeactivateUserUseCase(UserRepositoryImpl(db))
        user = await use_case.execute(user_id)
        log_info(
            "Account successfully deactivated",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id,
        )
        return user.__dict__

    except Exception as e:
        log_error(
            f"Unexpected error during account deactivation: {str(e)}",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id,
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/restore")
async def restore_me(
    data: RestoreRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    event_publisher: EventPublisher = Depends(get_event_publisher),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Account restore request",
        service="auth-service",
        request=request,
        trace_id=trace_id,
        context={"email": data.email},
    )

    try:
        repo = UserRepositoryImpl(db)
        token_repo = EmailTokenRepositoryImpl(db)
        user = await repo.get_by_email(data.email)

        if not user:
            log_warning(
                "User not found for restore request",
                service="auth-service",
                request=request,
                trace_id=trace_id,
                context={"email": data.email},
            )
            raise HTTPException(status_code=404, detail="User not found")

        if user.status != UserStatus.DEACTIVATED:
            log_warning(
                "User cannot be restored due to status",
                service="auth-service",
                request=request,
                user_id=user.id,
                trace_id=trace_id,
                context={"email": data.email, "user_status": user.status.value},
            )
            raise HTTPException(status_code=400, detail="User cannot be restored")

        use_case = RestoreUserUseCase(
            user_repo=repo, token_repo=token_repo, event_publisher=event_publisher
        )
        await use_case.execute(user_id=user.id)

        log_info(
            "Restore email sent successfully",
            service="auth-service",
            request=request,
            user_id=user.id,
            trace_id=trace_id,
            context={"email": data.email},
        )
        return {"message": "A recovery email has been sent to your address"}

    except Exception as e:
        log_error(
            f"Unexpected error during account restoration: {str(e)}",
            service="auth-service",
            request=request,
            trace_id=trace_id,
            context={"email": data.email},
        )
        raise HTTPException(status_code=500, detail="Internal server error")
