from fastapi import APIRouter, Depends, HTTPException, Request
from reforma_authorization.infrastructure.repositories.email_verification_token_impl import (
    EmailTokenRepositoryImpl,
)
from reforma_authorization.presentation.dependencies.get_event_publisher import (
    get_event_publisher,
)
from sqlalchemy.ext.asyncio import AsyncSession
from reforma_authorization.presentation.dependencies.get_db import get_db
from reforma_authorization.presentation.dependencies.get_current_user_id import (
    get_current_user_id,
)
from reforma_authorization.infrastructure.repositories.refresh_token_repository_impl import (
    RefreshTokenRepositoryImpl,
)
from reforma_authorization.infrastructure.repositories.user_repository_impl import (
    UserRepositoryImpl,
)
from reforma_authorization.infrastructure.security.password_hasher import (
    BcryptPasswordHasher,
)
from reforma_authorization.application.user.change_email_use_case import (
    ChangeEmailUseCase,
)
from reforma_authorization.application.user.change_username_use_case import (
    ChangeUsernameUseCase,
)
from reforma_authorization.application.user.change_password_use_case import (
    ChangePasswordUseCase,
)
from reforma_authorization.infrastructure.rabbitmq.publisher import EventPublisher
from reforma_authorization.presentation.schemas.change_requst import (
    ChangePasswordRequest,
    ChangeEmailRequest,
    ChangeUsernameRequest,
)
from reforma_common.logger import log_info, log_warning, log_error
from uuid import UUID

router = APIRouter(prefix="/user/change", tags=["Change"])


@router.put("/email")
async def change_email(
    data: ChangeEmailRequest,
    request: Request,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    event_publisher: EventPublisher = Depends(get_event_publisher),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Change email attempt",
        service="user-service",
        request=request,
        user_id=user_id,
        trace_id=trace_id,
        context={"new_email": data.new_email},
    )

    try:
        use_case = ChangeEmailUseCase(UserRepositoryImpl(db), event_publisher)
        result = await use_case.execute(user_id, data.new_email)

        log_info(
            "Email changed successfully",
            service="user-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id,
            context={"new_email": data.new_email},
        )
        return result

    except ValueError as e:
        log_warning(
            "Failed to change email",
            service="user-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id,
            context={"new_email": data.new_email, "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            f"Unexpected error during email change: {str(e)}",
            service="user-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id,
            context={"new_email": data.new_email},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/username")
async def change_username(
    data: ChangeUsernameRequest,
    request: Request,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    event_publisher: EventPublisher = Depends(get_event_publisher),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Change username attempt",
        service="user-service",
        request=request,
        user_id=user_id,
        trace_id=trace_id,
        context={"new_username": data.new_username},
    )

    try:
        use_case = ChangeUsernameUseCase(UserRepositoryImpl(db), event_publisher)
        result = await use_case.execute(user_id, data.new_username)

        log_info(
            "Username changed successfully",
            service="user-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id,
            context={"new_username": data.new_username},
        )
        return result

    except ValueError as e:
        log_warning(
            "Failed to change username",
            service="user-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id,
            context={"new_username": data.new_username, "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            f"Unexpected error during username change: {str(e)}",
            service="user-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id,
            context={"new_username": data.new_username},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/password")
async def change_password(
    request: Request,
    data: ChangePasswordRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    event_publisher: EventPublisher = Depends(get_event_publisher),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Change password attempt",
        service="user-service",
        request=request,
        user_id=user_id,
        trace_id=trace_id,
    )

    try:
        use_case = ChangePasswordUseCase(
            user_repo=UserRepositoryImpl(db),
            refresh_token_repo=RefreshTokenRepositoryImpl(db),
            token_repo=EmailTokenRepositoryImpl(db),
            password_hasher=BcryptPasswordHasher(),
            event_publisher=event_publisher,
        )
        await use_case.execute(user_id, data.old_password, data.new_password)

        log_info(
            "Password changed successfully",
            service="user-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id,
        )
        return {"message": "Please confirm the email to complete password change."}

    except ValueError as e:
        log_warning(
            "Failed to change password",
            service="user-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id,
            context={"error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            f"Unexpected error during password change: {str(e)}",
            service="user-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id,
        )
        raise HTTPException(status_code=500, detail="Internal server error")
