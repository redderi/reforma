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

router = APIRouter(prefix="/user", tags=["User"])

@router.put("/email")
async def change_email(
    data: ChangeEmailRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        return ChangeEmailUseCase(
            UserRepositoryImpl(db)
        ).execute(user_id, data.new_email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/username")
async def change_username(
    data: ChangeUsernameRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        return ChangeUsernameUseCase(
            UserRepositoryImpl(db)
        ).execute(user_id, data.new_username)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/password")
async def change_password(
    data: ChangePasswordRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        ChangePasswordUseCase(
            UserRepositoryImpl(db),
            RefreshTokenRepositoryImpl(db),
            BcryptPasswordHasher()
        ).execute(user_id, data.old_password, data.new_password)
        return {"detail": "Password updated"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/delete")
async def delete_user(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        DeleteUserUseCase(UserRepositoryImpl(db), RefreshTokenRepositoryImpl(db)).execute(user_id)
        return {"detail": "User deleted successfully."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
