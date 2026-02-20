from reforma_authorization.domain.repositories.user_repository import UserRepository
from uuid import UUID

class SoftDeleteUserByIdUseCase:

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self, user_id: UUID):
        return await self.user_repo.delete_by_id(user_id)
