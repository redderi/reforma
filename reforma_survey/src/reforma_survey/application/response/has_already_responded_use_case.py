from uuid import UUID
from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class HasAlreadyRespondedUseCase:
    def __init__(self, repository: ResponseRepository):
        self.repository = repository

    async def execute(
        self,
        survey_id: UUID,
        user_id: UUID | None = None,
        anonymous_id: str | None = None,
        ip_address: str | None = None,
        fingerprint: str | None = None,
    ) -> bool:
        async with SessionLocal() as db:
            async with db.begin():
                has = await self.repository.has_already_responded(
                    survey_id=survey_id,
                    user_id=user_id,
                    anonymous_id=anonymous_id,
                    ip_address=ip_address,
                    fingerprint=fingerprint,
                )
                return has
