from fastapi import APIRouter, Depends, HTTPException, Request
from reforma_authorization.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from reforma_authorization.application.admin.promote_user_use_case import PromoteUserUseCase
from reforma_authorization.application.admin.get_all_users_use_case import GetAllUsersUseCase
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
from reforma_authorization.presentation.dependencies.get_event_publisher import get_event_publisher
from reforma_common.logger import log_error, log_info, log_warning
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from reforma_authorization.presentation.dependencies.require_roles import require_roles
from reforma_common.roles import UserRole
from reforma_authorization.presentation.dependencies.get_db import get_db

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.patch("/users/{user_id}/promote")
async def promote_user(
    request: Request,
    user_id: UUID,
    data: PromoteRequest,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.ADMIN.value))
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Promote user attempt",
        service="auth-service",
        request=request,
        user_id=user_id,
        trace_id=trace_id,
        context={"new_role": data.new_role}
    )

    try:
        use_case = PromoteUserUseCase(UserRepositoryImpl(db))
        user = await use_case.execute(user_id=user_id, new_role=data.new_role)

        log_info(
            "User promoted successfully",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id,
            context={"new_role": data.new_role}
        )
        return {"detail": f"User {user.id} promoted to {user.role}"}

    except ValueError as e:
        log_warning(
            "Promote user failed",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id,
            context={
                "new_role": data.new_role,
                "error_detail": str(e)
            }
        )
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        log_error(
            f"Unexpected error during promote: {str(e)}",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id,
            context={"new_role": data.new_role}
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/users")
async def get_all_users(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.ADMIN.value))
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Request to retrieve all users",
        service="auth-service",
        request=request,
        trace_id=trace_id
    )

    try:
        use_case = GetAllUsersUseCase(UserRepositoryImpl(db))
        users = await use_case.execute()

        log_info(
            f"Successfully retrieved {len(users)} users",
            service="auth-service",
            request=request,
            trace_id=trace_id,
            context={"user_count": len(users)}
        )
        return [user.__dict__ for user in users]

    except Exception as e:
        log_error(
            f"Error retrieving all users: {str(e)}",
            service="auth-service",
            request=request,
            trace_id=trace_id
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/users/{user_id}")
async def get_user_by_id(
    request: Request,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.ADMIN.value))
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Request to retrieve user by ID",
        service="auth-service",
        request=request,
        user_id=user_id,
        trace_id=trace_id
    )

    try:
        use_case = GetUserByIdUseCase(UserRepositoryImpl(db))
        user = await use_case.execute(user_id)

        log_info(
            "User retrieved successfully",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id
        )
        return user.__dict__

    except ValueError as e:
        log_warning(
            "User not found by ID",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id,
            context={"error_detail": str(e)}
        )
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        log_error(
            f"Unexpected error retrieving user by ID: {str(e)}",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/users/{user_id}/soft-delete")
async def soft_delete_user(
    request: Request,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.ADMIN.value))
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Soft-delete user attempt",
        service="auth-service",
        request=request,
        user_id=user_id,
        trace_id=trace_id
    )

    try:
        use_case = SoftDeleteUserByIdUseCase(UserRepositoryImpl(db))
        await use_case.execute(user_id)

        log_info(
            "User successfully soft-deleted",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id
        )
        return {"detail": f"User {user_id} soft-deleted"}

    except ValueError as e:
        log_warning(
            "Soft-delete failed",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id,
            context={"error_detail": str(e)}
        )
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        log_error(
            f"Unexpected error during soft-delete: {str(e)}",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/users/{user_id}/hard-delete")
async def hard_delete_user(
    request: Request,
    user_id: UUID,
    event_publisher: EventPublisher = Depends(get_event_publisher),
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.ADMIN.value))
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Hard-delete user attempt",
        service="auth-service",
        request=request,
        user_id=user_id,
        trace_id=trace_id
    )

    try:
        use_case = HardDeleteUserByIdUseCase(
            UserRepositoryImpl(db),
            event_publisher
        )
        await use_case.execute(user_id)

        log_info(
            "User successfully hard-deleted",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id
        )
        return {"detail": "User deleted successfully."}

    except ValueError as e:
        log_warning(
            "Hard-delete failed",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id,
            context={"error_detail": str(e)}
        )
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        log_error(
            f"Unexpected error during hard-delete: {str(e)}",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/users/{user_id}/activate")
async def activate_user(
    request: Request,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.ADMIN.value))
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Activate user attempt",
        service="auth-service",
        request=request,
        user_id=user_id,
        trace_id=trace_id
    )

    try:
        use_case = ActivateUserUseCase(UserRepositoryImpl(db))
        user = await use_case.execute(user_id)

        log_info(
            "User activated successfully",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id
        )
        return user.__dict__

    except ValueError as e:
        log_warning(
            "User activation failed",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id,
            context={"error_detail": str(e)}
        )
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        log_error(
            f"Unexpected error during user activation: {str(e)}",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/users/{user_id}/suspend")
async def suspend_user(
    request: Request,
    user_id: UUID,
    data: SuspendRequest,
    admin_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.ADMIN.value))
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Suspend user attempt",
        service="auth-service",
        request=request,
        user_id=user_id,
        trace_id=trace_id,
        context={"reason": data.reason}
    )

    try:
        use_case = SuspendUserUseCase(UserRepositoryImpl(db))
        user = await use_case.execute(user_id=user_id, reason=data.reason, admin_id=admin_id)

        log_info(
            "User suspended successfully",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id,
            context={"reason": data.reason}
        )
        return user.__dict__

    except ValueError as e:
        log_warning(
            "User suspension failed",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id,
            context={
                "reason": data.reason,
                "error_detail": str(e)
            }
        )
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        log_error(
            f"Unexpected error during user suspension: {str(e)}",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id,
            context={"reason": data.reason}
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    request: Request,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.ADMIN.value))
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Deactivate user attempt",
        service="auth-service",
        request=request,
        user_id=user_id,
        trace_id=trace_id
    )

    try:
        use_case = DeactivateUserUseCase(UserRepositoryImpl(db))
        user = await use_case.execute(user_id)

        log_info(
            "User deactivated successfully",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id
        )
        return user.__dict__

    except ValueError as e:
        log_warning(
            "User deactivation failed",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id,
            context={"error_detail": str(e)}
        )
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        log_error(
            f"Unexpected error during user deactivation: {str(e)}",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/users/{user_id}/restore")
async def restore_user(
    request: Request,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.ADMIN.value))
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Restore user attempt",
        service="auth-service",
        request=request,
        user_id=user_id,
        trace_id=trace_id
    )

    try:
        use_case = RestoreUserByAdminUseCase(UserRepositoryImpl(db))
        user = await use_case.execute(user_id)

        log_info(
            "User restored successfully",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id
        )
        return user.__dict__

    except ValueError as e:
        log_warning(
            "User restore failed",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id,
            context={"error_detail": str(e)}
        )
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        log_error(
            f"Unexpected error during user restore: {str(e)}",
            service="auth-service",
            request=request,
            user_id=user_id,
            trace_id=trace_id
        )
        raise HTTPException(status_code=500, detail="Internal server error")