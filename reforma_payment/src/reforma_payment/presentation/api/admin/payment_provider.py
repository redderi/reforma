from fastapi import APIRouter, Depends, HTTPException, Request
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from reforma_payment.domain.entities.payment_provider import PaymentProvider
from reforma_payment.application.payment_provider.add_payment_provider_use_case import (
    AddPaymentProviderUseCase,
)
from reforma_payment.application.payment_provider.get_payment_provider_by_id_use_case import (
    GetPaymentProviderByIdUseCase,
)
from reforma_payment.application.payment_provider.update_payment_provider_use_case import (
    UpdatePaymentProviderUseCase,
)
from reforma_payment.application.payment_provider.activate_payment_provider_use_case import (
    ActivatePaymentProviderUseCase,
)
from reforma_payment.application.payment_provider.deactivate_payment_provider_use_case import (
    DeactivatePaymentProviderUseCase,
)
from reforma_payment.application.payment_provider.delete_payment_provider_use_case import (
    DeletePaymentProviderUseCase,
)
from reforma_payment.application.payment_provider.get_active_provider_by_type_use_case import (
    GetActiveProviderByTypeUseCase,
)
from reforma_payment.infrastructure.repositories.payment_provider_repository_impl import (
    PaymentProviderRepositoryImpl,
)
from reforma_payment.presentation.dependencies.get_db import get_db
from reforma_common.logger import log_info, log_warning, log_error
from reforma_payment.presentation.dependencies.require_roles import require_roles
from reforma_common.roles import UserRole

router = APIRouter(prefix="/admin/payment-providers", tags=["AdminPaymentProvider"])


@router.post("/", response_model=PaymentProvider)
async def add_payment_provider(
    request: Request,
    provider: PaymentProvider,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(UserRole.ADMIN.value)),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Add payment provider attempt",
        service="payment-service",
        request=request,
        trace_id=trace_id,
        context={"provider_type": provider.provider_type},
    )

    try:
        use_case = AddPaymentProviderUseCase(PaymentProviderRepositoryImpl(db))
        new_provider = await use_case.execute(provider)

        log_info(
            "Payment provider added successfully",
            service="payment-service",
            request=request,
            trace_id=trace_id,
            context={
                "provider_id": str(new_provider.id),
                "provider_type": new_provider.provider_type,
            },
        )
        return new_provider

    except Exception as e:
        log_error(
            "Error adding payment provider",
            service="payment-service",
            request=request,
            trace_id=trace_id,
            context={"provider_type": provider.provider_type, "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{provider_id}", response_model=PaymentProvider)
async def get_payment_provider_by_id(
    request: Request,
    provider_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(UserRole.ADMIN.value)),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Get payment provider by ID request",
        service="payment-service",
        request=request,
        trace_id=trace_id,
        context={"provider_id": str(provider_id)},
    )

    try:
        use_case = GetPaymentProviderByIdUseCase(PaymentProviderRepositoryImpl(db))
        provider = await use_case.execute(provider_id)

        if not provider:
            log_warning(
                "Payment provider not found",
                service="payment-service",
                request=request,
                trace_id=trace_id,
                context={"provider_id": str(provider_id)},
            )
            raise HTTPException(status_code=404, detail="Payment provider not found")

        log_info(
            "Payment provider retrieved successfully",
            service="payment-service",
            request=request,
            trace_id=trace_id,
            context={"provider_id": str(provider_id)},
        )
        return provider

    except Exception as e:
        log_error(
            f"Error getting payment provider by ID: {e}",
            service="payment-service",
            request=request,
            trace_id=trace_id,
            context={"provider_id": str(provider_id)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{provider_id}", response_model=PaymentProvider)
async def update_payment_provider(
    request: Request,
    provider_id: UUID,
    provider_data: PaymentProvider,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(UserRole.ADMIN.value)),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Update payment provider attempt",
        service="payment-service",
        request=request,
        trace_id=trace_id,
        context={
            "provider_id": str(provider_id),
            "provider_type": provider_data.provider_type,
        },
    )

    try:
        use_case = UpdatePaymentProviderUseCase(PaymentProviderRepositoryImpl(db))
        provider_data.id = provider_id
        updated_provider = await use_case.execute(provider_data)

        log_info(
            "Payment provider updated successfully",
            service="payment-service",
            request=request,
            trace_id=trace_id,
            context={"provider_id": str(updated_provider.id)},
        )
        return updated_provider

    except Exception as e:
        log_error(
            "Error updating payment provider",
            service="payment-service",
            request=request,
            trace_id=trace_id,
            context={"provider_id": str(provider_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{provider_id}/activate")
async def activate_payment_provider(
    request: Request,
    provider_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(UserRole.ADMIN.value)),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Activate payment provider attempt",
        service="payment-service",
        request=request,
        trace_id=trace_id,
        context={"provider_id": str(provider_id)},
    )

    try:
        use_case = ActivatePaymentProviderUseCase(PaymentProviderRepositoryImpl(db))
        await use_case.execute(provider_id)

        log_info(
            "Payment provider activated successfully",
            service="payment-service",
            request=request,
            trace_id=trace_id,
            context={"provider_id": str(provider_id)},
        )
        return {"detail": "Payment provider activated successfully"}

    except Exception as e:
        log_error(
            "Error activating payment provider",
            service="payment-service",
            request=request,
            trace_id=trace_id,
            context={"provider_id": str(provider_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{provider_id}/deactivate")
async def deactivate_payment_provider(
    request: Request,
    provider_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(UserRole.ADMIN.value)),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Deactivate payment provider attempt",
        service="payment-service",
        request=request,
        trace_id=trace_id,
        context={"provider_id": str(provider_id)},
    )

    try:
        use_case = DeactivatePaymentProviderUseCase(PaymentProviderRepositoryImpl(db))
        await use_case.execute(provider_id)

        log_info(
            "Payment provider deactivated successfully",
            service="payment-service",
            request=request,
            trace_id=trace_id,
            context={"provider_id": str(provider_id)},
        )
        return {"detail": "Payment provider deactivated successfully"}

    except Exception as e:
        log_error(
            "Error deactivating payment provider",
            service="payment-service",
            request=request,
            trace_id=trace_id,
            context={"provider_id": str(provider_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{provider_id}")
async def delete_payment_provider(
    request: Request,
    provider_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(UserRole.ADMIN.value)),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Delete payment provider attempt",
        service="payment-service",
        request=request,
        trace_id=trace_id,
        context={"provider_id": str(provider_id)},
    )

    try:
        use_case = DeletePaymentProviderUseCase(PaymentProviderRepositoryImpl(db))
        await use_case.execute(provider_id)

        log_info(
            "Payment provider deleted successfully",
            service="payment-service",
            request=request,
            trace_id=trace_id,
            context={"provider_id": str(provider_id)},
        )
        return {"detail": "Payment provider deleted successfully"}

    except Exception as e:
        log_error(
            "Error deleting payment provider",
            service="payment-service",
            request=request,
            trace_id=trace_id,
            context={"provider_id": str(provider_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/active/{provider_type}", response_model=PaymentProvider)
async def get_active_provider_by_type(
    request: Request,
    provider_type: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(UserRole.ADMIN.value)),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Get active payment provider by type request",
        service="payment-service",
        request=request,
        trace_id=trace_id,
        context={"provider_type": provider_type},
    )

    try:
        use_case = GetActiveProviderByTypeUseCase(PaymentProviderRepositoryImpl(db))
        provider = await use_case.execute(provider_type)

        if not provider:
            log_warning(
                "No active payment provider found for type",
                service="payment-service",
                request=request,
                trace_id=trace_id,
                context={"provider_type": provider_type},
            )
            raise HTTPException(
                status_code=404, detail="Active payment provider not found"
            )

        log_info(
            "Active payment provider retrieved successfully",
            service="payment-service",
            request=request,
            trace_id=trace_id,
            context={"provider_id": str(provider.id)},
        )
        return provider

    except Exception as e:
        log_error(
            "Error getting active provider by type",
            service="payment-service",
            request=request,
            trace_id=trace_id,
            context={"provider_type": provider_type, "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")
