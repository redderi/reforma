from abc import ABC, abstractmethod
from uuid import UUID
from typing import Optional, List
from reforma_payment.domain.entities.payment_provider import PaymentProvider


class PaymentProviderRepository(ABC):

    @abstractmethod
    async def add(self, provider: PaymentProvider) -> PaymentProvider:
        pass

    @abstractmethod
    async def get_by_id(self, provider_id: UUID) -> Optional[PaymentProvider]:
        pass

    @abstractmethod
    async def get_active_by_type(self, provider_type: str) -> Optional[PaymentProvider]:
        pass

    @abstractmethod
    async def list_active(self) -> List[PaymentProvider]:
        pass

    @abstractmethod
    async def update(self, provider: PaymentProvider) -> PaymentProvider:
        pass

    @abstractmethod
    async def activate(self, provider_id: UUID) -> None:
        pass

    @abstractmethod
    async def deactivate(self, provider_id: UUID) -> None:
        pass

    @abstractmethod
    async def delete(self, provider_id: UUID) -> None:
        pass