from tuned.repository.user import UserRepository
from tuned.repository.blogs import BlogRepository

class Repository:
    def __init__(self):
        self._user = None
        self._blog = None

    @property
    def user(self) -> UserRepository:
        if not self._user:
            self._user = UserRepository
        return self._user

    @property
    def blog(self) -> BlogRepository:
        if not self._blog:
            self._blog = BlogRepository
        return self._blog
