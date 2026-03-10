from tuned.repository.user import UserRepository


class Repository:
    def __init__(self):
        self._user = None

    @property
    def user(self) -> UserRepository:
        if not self._user:
            self._user = UserRepository
        return self._user