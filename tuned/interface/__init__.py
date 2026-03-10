from tuned.interface.users import UserService

class Services:
    def __init__(self) -> None:
        self._user = None

    def user(self) -> UserService:
        if not self._user:
            self._user = UserService
        return self._user
    
