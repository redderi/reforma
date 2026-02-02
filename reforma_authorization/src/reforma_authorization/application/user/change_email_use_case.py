from reforma_authorization.domain.repositories.user_repository import UserRepository

class ChangeEmailUseCase:

    def __init__(self, user_repo:UserRepository):
        self.user_repo = user_repo

    def execute(self, user_id: int, new_email: str):
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        if self.user_repo.get_by_email(new_email):
            raise ValueError("Email already exists")

        return self.user_repo.change_email(user, new_email)