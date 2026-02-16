from fastapi import APIRouter, Depends, HTTPException
from reforma_authorization.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from reforma_authorization.application.admin.promote_user_use_case import PromoteUserUseCase
from reforma_authorization.application.admin.get_all_users_use_case import GetAllUsersUseCase
from reforma_authorization.infrastructure.repositories.refresh_token_repository_impl import RefreshTokenRepositoryImpl
from reforma_authorization.infrastructure.rabbitmq.publisher import EventPublisher
from reforma_authorization.presentation.schemas.auth_request import PromoteRequest, SuspendRequest
from reforma_authorization.presentation.dependencies.get_current_user_id import get_current_user_id
from reforma_authorization.application.admin.activate_user_use_case import ActivateUserUseCase
from reforma_authorization.application.admin.deactivate_user_use_case import DeactivateUserUseCase
from reforma_authorization.application.admin.get_user_by_id_use_case import GetUserByIdUseCase
from reforma_authorization.application.admin.restore_user_by_admin_use_case import RestoreUserByAdminUseCase
from reforma_authorization.application.admin.suspend_user_use_case import SuspendUserUseCase
from reforma_authorization.application.admin.hard_delete_use_case import HardDeleteUserByIdUseCase
from reforma_authorization.application.admin.soft_delete_user_by_id_use_case import SoftDeleteUserByIdUseCase
from reforma_common.logger import log_error, log_info, log_warning
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from reforma_authorization.infrastructure.db.models import UserModel
from reforma_authorization.presentation.dependencies.require_roles import require_roles
from reforma_common.roles import UserRole
from reforma_authorization.presentation.dependencies.get_db import get_db
event_publisher = EventPublisher()

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.patch("/users/{user_id}/promote")
async def promote_user(
    user_id: UUID,
    request: PromoteRequest,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.ADMIN.value))
):
    log_info(f"Promote user attempt: {user_id} to role {request.new_role}", service="auth-service")
    try:
        use_case = PromoteUserUseCase(UserRepositoryImpl(db))
        user = await use_case.execute(user_id=user_id, new_role=request.new_role)
        log_info(f"User promoted: {user.id}", service="auth-service")
        return {"detail": f"User {user.id} promoted to {user.role}"}
    except ValueError as e:
        log_warning(f"Promote user failed: {e}", service="auth-service")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        log_error(f"Unexpected error during promote: {e}", service="auth-service")
        raise HTTPException(status_code=500, detail="Internal server error")



@router.get("/users")
async def get_all_users(
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.ADMIN.value))
):
    try:
        use_case = GetAllUsersUseCase(UserRepositoryImpl(db))
        users = await use_case.execute()
        return [user.__dict__ for user in users]
    except Exception as e:
        log_error(f"Get all users error: {e}", service="auth-service")
        raise HTTPException(status_code=500, detail="Internal server error")
    

@router.get("/users/{user_id}")
async def get_user_by_id(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.ADMIN.value))
):
    try:
        use_case = GetUserByIdUseCase(UserRepositoryImpl(db))
        user = await use_case.execute(user_id)
        return user.__dict__
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        log_error(f"Get user by id error: {e}", service="auth-service")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/users/{user_id}/soft-delete")
async def soft_delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.ADMIN.value))
):
    try:
        use_case = SoftDeleteUserByIdUseCase(UserRepositoryImpl(db))
        await use_case.execute(user_id)
        log_info(f"User soft-deleted: {user_id}", service="auth-service")
        return {"detail": f"User {user_id} soft-deleted"}
    except ValueError as e:
        log_warning(f"Soft delete failed: {e}", service="auth-service")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        log_error   (f"Soft delete unexpected error: {e}", service="auth-service")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@router.delete("/users/{user_id}/hard-delete")
async def hard_delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.ADMIN.value))
):
    log_info(f"Hard delete user attempt: {user_id}", service="auth-service")
    try:
        use_case = HardDeleteUserByIdUseCase(
            UserRepositoryImpl(db),
            event_publisher
        )
        await use_case.execute(user_id)
        log_info(f"User hard-deleted: {user_id}", service="auth-service")
        return {"detail": "User deleted successfully."}
    except ValueError as e:
        log_warning(f"Hard delete failed: {e}", service="auth-service")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        log_error(f"Hard delete unexpected error: {e}", service="auth-service")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.ADMIN.value))
):
    try:
        use_case = ActivateUserUseCase(UserRepositoryImpl(db))
        user = await use_case.execute(user_id)
        log_info(f"User activated: {user.id}", service="auth-service")
        return user.__dict__
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: UUID,
    request: SuspendRequest,
    admin_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.ADMIN.value))
):
    try:
        use_case = SuspendUserUseCase(UserRepositoryImpl(db))
        user = await use_case.execute(user_id=user_id, reason=request.reason, admin_id=admin_id)
        log_info(f"User suspended: {user.id}", service="auth-service")
        return user.__dict__
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.ADMIN.value))
):
    try:
        use_case = DeactivateUserUseCase(UserRepositoryImpl(db))
        user = await use_case.execute(user_id)
        log_info(f"User deactivated: {user.id}", service="auth-service")
        return user.__dict__
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/users/{user_id}/restore")
async def restore_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.ADMIN.value))
):
    try:
        use_case = RestoreUserByAdminUseCase(UserRepositoryImpl(db))
        user = await use_case.execute(user_id)
        log_info(f"User restored: {user_id}", service="auth-service")
        return user.__dict__
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
