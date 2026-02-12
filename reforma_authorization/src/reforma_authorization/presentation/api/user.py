from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from reforma_authorization.presentation.dependencies.get_db import get_db
from reforma_authorization.presentation.dependencies.current_user import get_current_user_id
from reforma_authorization.infrastructure.repositories.refresh_token_repository_impl import RefreshTokenRepositoryImpl
from reforma_authorization.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from reforma_authorization.infrastructure.security.password_hasher import BcryptPasswordHasher
from reforma_authorization.application.user.delete_user_use_case import DeleteUserUseCase
from reforma_authorization.application.user.change_email_use_case import ChangeEmailUseCase
from reforma_authorization.application.user.change_username_use_case import ChangeUsernameUseCase
from reforma_authorization.application.user.change_password_use_case import ChangePasswordUseCase
from reforma_authorization.presentation.schemas.change_requst import (
    ChangePasswordRequest,
    ChangeEmailRequest,
    ChangeUsernameRequest
)
from reforma_authorization.common.logger import log_info, log_warning, log_error 

router = APIRouter(prefix="/user/change", tags=["User"])

@router.put("/email")
async def change_email(
    data: ChangeEmailRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    log_info(f"Change email attempt for user_id={user_id}", service="user-service", context={"new_email": data.new_email})
    try:
        result = ChangeEmailUseCase(UserRepositoryImpl(db)).execute(user_id, data.new_email)
        log_info(f"Email changed successfully for user_id={user_id}", service="user-service")
        return result
    except ValueError as e:
        log_warning(f"Failed to change email for user_id={user_id}: {e}", service="user-service")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Unexpected error changing email for user_id={user_id}: {e}", service="user-service")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/username")
async def change_username(
    data: ChangeUsernameRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    log_info(f"Change username attempt for user_id={user_id}", service="user-service", context={"new_username": data.new_username})
    try:
        result = ChangeUsernameUseCase(UserRepositoryImpl(db)).execute(user_id, data.new_username)
        log_info(f"Username changed successfully for user_id={user_id}", service="user-service")
        return result
    except ValueError as e:
        log_warning(f"Failed to change username for user_id={user_id}: {e}", service="user-service")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Unexpected error changing username for user_id={user_id}: {e}", service="user-service")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/password")
async def change_password(
    data: ChangePasswordRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    log_info(f"Change password attempt for user_id={user_id}", service="user-service")
    try:
        ChangePasswordUseCase(
            UserRepositoryImpl(db),
            RefreshTokenRepositoryImpl(db),
            BcryptPasswordHasher()
        ).execute(user_id, data.old_password, data.new_password)
        log_info(f"Password changed successfully for user_id={user_id}", service="user-service")
        return {"detail": "Password updated"}
    except ValueError as e:
        log_warning(f"Failed to change password for user_id={user_id}: {e}", service="user-service")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Unexpected error changing password for user_id={user_id}: {e}", service="user-service")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/delete")
async def delete_user(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    log_info(f"Delete user attempt for user_id={user_id}", service="user-service")
    try:
        DeleteUserUseCase(UserRepositoryImpl(db), RefreshTokenRepositoryImpl(db)).execute(user_id)
        log_info(f"User deleted successfully: user_id={user_id}", service="user-service")
        return {"detail": "User deleted successfully."}
    except ValueError as e:
        log_warning(f"Failed to delete user user_id={user_id}: {e}", service="user-service")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        log_error(f"Unexpected error deleting user user_id={user_id}: {e}", service="user-service")
        raise HTTPException(status_code=500, detail="Internal server error")