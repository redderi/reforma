from reforma_authorization.domain.repositories.user_repository import UserRepository
from uuid import UUID


class GetUserByIdUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self, user_id: UUID):
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        return user
