from reforma_survey.infrastructure.repositories.user_profile_repository_impl import (
    UserProfileRepositoryImpl,
)
from reforma_survey.infrastructure.db.session import SessionLocal


class AddBalanceHandler:
    async def handle(self, payload: dict):
        user_id = payload.get("user_id")
        amount = payload.get("amount")
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    repo = UserProfileRepositoryImpl(db)
                    await repo.add_balance(user_id=user_id, amount=amount)
                except Exception:
                    raise
