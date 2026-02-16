from uuid import UUID
from reforma_authorization.domain.repositories.user_repository import UserRepository
from reforma_common.roles import UserRole

class PromoteUserUseCase:

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: UUID, new_role: UserRole):
        user = await self.user_repository.get_by_id(user_id)

        if not user:
            raise ValueError("User not found")

        user.role = new_role
        await self.user_repository.update(user)

        return user
