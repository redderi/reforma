from fastapi import APIRouter, Depends, HTTPException, Query
from reforma_authorization.infrastructure.repositories.email_verification_token_impl import EmailTokenRepositoryImpl
from reforma_authorization.application.user.soft_delete_use_case import SoftDeleteUserUseCase
from reforma_authorization.application.admin.deactivate_user_use_case import DeactivateUserUseCase
from reforma_authorization.presentation.schemas.auth_request import RestoreRequest
from reforma_common.user_status import UserStatus
from sqlalchemy.ext.asyncio import AsyncSession
from reforma_authorization.presentation.dependencies.get_db import get_db
from reforma_authorization.presentation.dependencies.get_current_user_id import get_current_user_id
from reforma_authorization.infrastructure.repositories.refresh_token_repository_impl import RefreshTokenRepositoryImpl
from reforma_authorization.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from reforma_authorization.infrastructure.security.password_hasher import BcryptPasswordHasher
from reforma_authorization.application.user.change_email_use_case import ChangeEmailUseCase
from reforma_authorization.application.user.change_username_use_case import ChangeUsernameUseCase
from reforma_authorization.application.user.change_password_use_case import ChangePasswordUseCase
from reforma_authorization.infrastructure.rabbitmq.publisher import EventPublisher
from reforma_authorization.presentation.schemas.change_requst import (
    ChangePasswordRequest,
    ChangeEmailRequest,
    ChangeUsernameRequest
)
from reforma_common.logger import log_info, log_warning, log_error
from uuid import UUID

router = APIRouter(prefix="/user/change", tags=["Change"])
event_publisher = EventPublisher()

# ----------------- Change Email -----------------
@router.put("/email")
async def change_email(
    data: ChangeEmailRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Change email attempt for user_id={user_id}", service="user-service", context={"new_email": data.new_email})
    try:
        use_case = ChangeEmailUseCase(UserRepositoryImpl(db), event_publisher)
        result = await use_case.execute(user_id, data.new_email)
        log_info(f"Email changed successfully for user_id={user_id}", service="user-service")
        return result
    except ValueError as e:
        log_warning(f"Failed to change email for user_id={user_id}: {e}", service="user-service")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Unexpected error changing email for user_id={user_id}: {e}", service="user-service")
        raise HTTPException(status_code=500, detail="Internal server error")


# ----------------- Change Username -----------------
@router.put("/username")
async def change_username(
    data: ChangeUsernameRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Change username attempt for user_id={user_id}", service="user-service", context={"new_username": data.new_username})
    try:
        use_case = ChangeUsernameUseCase(UserRepositoryImpl(db), event_publisher)
        result = await use_case.execute(user_id, data.new_username)
        log_info(f"Username changed successfully for user_id={user_id}", service="user-service")
        return result
    except ValueError as e:
        log_warning(f"Failed to change username for user_id={user_id}: {e}", service="user-service")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Unexpected error changing username for user_id={user_id}: {e}", service="user-service")
        raise HTTPException(status_code=500, detail="Internal server error")


# ----------------- Change Password -----------------
@router.put("/password")
async def change_password(
    data: ChangePasswordRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Change password attempt for user_id={user_id}", service="user-service")
    try:
        use_case = ChangePasswordUseCase(
            user_repo=UserRepositoryImpl(db),
            refresh_token_repo=RefreshTokenRepositoryImpl(db),
            token_repo=EmailTokenRepositoryImpl(db),
            password_hasher=BcryptPasswordHasher(),
            event_publisher=event_publisher
        )
        await use_case.execute(user_id, data.old_password, data.new_password)
        log_info(f"Password changed successfully for user_id={user_id}", service="user-service")
        return {"message": "Подтвердите письмо в email, чтобы завершить смену пароля."}
    except ValueError as e:
        log_warning(f"Failed to change password for user_id={user_id}: {e}", service="user-service")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Unexpected error changing password for user_id={user_id}: {e}", service="user-service")
        raise HTTPException(status_code=500, detail="Internal server error")
