from abc import ABC, abstractmethod
from datetime import datetime
from typing import List
from uuid import UUID

from reforma_payment.domain.entities.payment import Payment


class PaymentRepository(ABC):
    @abstractmethod
    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        pass

    @abstractmethod
    async def get_by_external_id(self, external_id: str) -> Payment | None:
        pass

    @abstractmethod
    async def find_by_idempotency(self, idempotency_key: str) -> Payment | None:
        pass

    @abstractmethod
    async def get_by_user(
        self, user_id: UUID, limit: int = 20, offset: int = 0
    ) -> List[Payment]:
        pass

    @abstractmethod
    async def get_pending_by_user(self, user_id: UUID) -> List[Payment]:
        pass

    @abstractmethod
    async def create(self, payment: Payment) -> Payment:
        pass

    @abstractmethod
    async def update_status(
        self,
        payment_id: UUID,
        new_status: str,
        external_id: str | None = None,
        redirect_url: str | None = None,
        client_secret: str | None = None,
        updated_at: datetime | None = None,
    ) -> Payment:
        pass

    @abstractmethod
    async def mark_as_succeeded(
        self, payment_id: UUID, external_id: str, completed_at: datetime
    ) -> Payment:
        pass

    @abstractmethod
    async def mark_as_failed(
        self,
        payment_id: UUID,
        error_message: str | None = None,
        completed_at: datetime | None = None,
    ) -> Payment:
        pass

    @abstractmethod
    async def exists(self, payment_id: UUID) -> bool:
        pass

    @abstractmethod
    async def count_by_user(self, user_id: UUID) -> int:
        pass

    @abstractmethod
    async def count_pending_by_user(self, user_id: UUID) -> int:
        pass
