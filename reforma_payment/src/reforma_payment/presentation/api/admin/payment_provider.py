from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from reforma_payment.domain.entities.payment_provider import PaymentProvider
from reforma_payment.application.payment_provider.add_payment_provider_use_case import AddPaymentProviderUseCase
from reforma_payment.application.payment_provider.get_payment_provider_by_id_use_case import GetPaymentProviderByIdUseCase
from reforma_payment.application.payment_provider.update_payment_provider_use_case import UpdatePaymentProviderUseCase
from reforma_payment.application.payment_provider.activate_payment_provider_use_case import ActivatePaymentProviderUseCase
from reforma_payment.application.payment_provider.deactivate_payment_provider_use_case import DeactivatePaymentProviderUseCase
from reforma_payment.application.payment_provider.delete_payment_provider_use_case import DeletePaymentProviderUseCase
from reforma_payment.application.payment_provider.get_active_provider_by_type_use_case import GetActiveProviderByTypeUseCase
from reforma_payment.infrastructure.repositories.payment_provider_repository_impl import PaymentProviderRepositoryImpl
from reforma_payment.presentation.dependencies.get_db import get_db
from reforma_common.logger import log_info, log_warning, log_error
from reforma_payment.presentation.dependencies.require_roles import require_roles
from reforma_common.roles import UserRole

router = APIRouter(prefix="/admin/payment-providers", tags=["AdminPaymentProvider"])

@router.post("/", response_model=PaymentProvider)
async def add_payment_provider(
    provider: PaymentProvider,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.ADMIN.value))
):
    try:
        use_case = AddPaymentProviderUseCase(PaymentProviderRepositoryImpl(db))
        new_provider = await use_case.execute(provider)
        log_info(f"Payment provider added: {new_provider.id}", service="payment-service")
        return new_provider
    except Exception as e:
        log_error(f"Error adding payment provider: {e}", service="payment-service")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{provider_id}", response_model=PaymentProvider)
async def get_payment_provider_by_id(
    provider_id: UUID,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.ADMIN.value))
):
    try:
        use_case = GetPaymentProviderByIdUseCase(PaymentProviderRepositoryImpl(db))
        provider = await use_case.execute(provider_id)
        if not provider:
            log_warning(f"Payment provider not found: {provider_id}", service="payment-service")
            raise HTTPException(status_code=404, detail="Payment provider not found")
        return provider
    except Exception as e:
        log_error(f"Error getting payment provider by id: {e}", service="payment-service")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{provider_id}", response_model=PaymentProvider)
async def update_payment_provider(
    provider_id: UUID,
    provider_data: PaymentProvider,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.ADMIN.value))
):
    try:
        use_case = UpdatePaymentProviderUseCase(PaymentProviderRepositoryImpl(db))
        provider_data.id = provider_id  
        updated_provider = await use_case.execute(provider_data)
        log_info(f"Payment provider updated: {updated_provider.id}", service="payment-service")
        return updated_provider
    except Exception as e:
        log_error(f"Error updating payment provider {provider_id}: {e}", service="payment-service")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{provider_id}/activate")
async def activate_payment_provider(
    provider_id: UUID,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.ADMIN.value))
):
    try:
        use_case = ActivatePaymentProviderUseCase(PaymentProviderRepositoryImpl(db))
        await use_case.execute(provider_id)
        log_info(f"Payment provider activated: {provider_id}", service="payment-service")
        return {"detail": "Payment provider activated successfully"}
    except Exception as e:
        log_error(f"Error activating payment provider {provider_id}: {e}", service="payment-service")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{provider_id}/deactivate")
async def deactivate_payment_provider(
    provider_id: UUID,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.ADMIN.value))
):
    try:
        use_case = DeactivatePaymentProviderUseCase(PaymentProviderRepositoryImpl(db))
        await use_case.execute(provider_id)
        log_info(f"Payment provider deactivated: {provider_id}", service="payment-service")
        return {"detail": "Payment provider deactivated successfully"}
    except Exception as e:
        log_error(f"Error deactivating payment provider {provider_id}: {e}", service="payment-service")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{provider_id}")
async def delete_payment_provider(
    provider_id: UUID,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.ADMIN.value))
):
    try:
        use_case = DeletePaymentProviderUseCase(PaymentProviderRepositoryImpl(db))
        await use_case.execute(provider_id)
        log_info(f"Payment provider deleted: {provider_id}", service="payment-service")
        return {"detail": "Payment provider deleted successfully"}
    except Exception as e:
        log_error(f"Error deleting payment provider {provider_id}: {e}", service="payment-service")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/active/{provider_type}", response_model=PaymentProvider)
async def get_active_provider_by_type(
    provider_type: str,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.ADMIN.value))
):
    try:
        use_case = GetActiveProviderByTypeUseCase(PaymentProviderRepositoryImpl(db))
        provider = await use_case.execute(provider_type)
        if not provider:
            log_warning(f"No active payment provider found for type: {provider_type}", service="payment-service")
            raise HTTPException(status_code=404, detail="Active payment provider not found")
        return provider
    except Exception as e:
        log_error(f"Error getting active provider by type {provider_type}: {e}", service="payment-service")
        raise HTTPException(status_code=500, detail="Internal server error")
