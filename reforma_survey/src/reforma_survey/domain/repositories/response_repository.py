from abc import ABC, abstractmethod
from typing import Any, List, Dict
from uuid import UUID
from datetime import datetime
from reforma_survey.domain.entities.response import Response


class ResponseRepository(ABC):
    @abstractmethod
    async def get_by_id(self, response_id: UUID) -> Response | None:
        pass

    @abstractmethod
    async def get_by_survey(
        self,
        survey_id: UUID,
        limit: int = 100,
        offset: int = 0,
        include_anonymous: bool = True,
    ) -> List[Response]:
        pass

    @abstractmethod
    async def get_by_user_and_survey(
        self,
        survey_id: UUID,
        user_id: UUID | None = None,
        anonymous_id: str | None = None,
    ) -> Response | None:
        pass

    @abstractmethod
    async def get_latest_by_user(
        self, user_id: UUID, limit: int = 10
    ) -> List[Response]:
        pass

    @abstractmethod
    async def has_already_responded(
        self,
        survey_id: UUID,
        user_id: UUID | None = None,
        anonymous_id: str | None = None,
        ip_address: str | None = None,
        fingerprint: str | None = None,
    ) -> bool:
        pass

    @abstractmethod
    async def create(self, response: Response) -> Response:
        pass

    @abstractmethod
    async def update_answers(
        self, response_id: UUID, new_answers: Dict[UUID, Any]
    ) -> Response:
        pass

    @abstractmethod
    async def mark_submitted(
        self, response_id: UUID, submitted_at: datetime = None
    ) -> Response:
        pass

    @abstractmethod
    async def delete(self, response_id: UUID) -> None:
        pass

    @abstractmethod
    async def count_by_survey(self, survey_id: UUID) -> int:
        pass

    @abstractmethod
    async def count_unique_users_by_survey(self, survey_id: UUID) -> int:
        pass

    @abstractmethod
    async def count_by_user(self, user_id: UUID) -> int:
        pass

    @abstractmethod
    async def count_anonymous_by_survey(self, survey_id: UUID) -> int:
        pass
