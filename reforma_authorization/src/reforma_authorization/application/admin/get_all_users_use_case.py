from reforma_authorization.domain.repositories.user_repository import UserRepository


class GetAllUsersUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self):
        return await self.user_repo.get_all()
