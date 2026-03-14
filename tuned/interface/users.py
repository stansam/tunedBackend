from typing import Tuple, Optional
from datetime import datetime, timezone, timedelta
from flask_login import login_user
from tuned.models.user import User
from tuned.repository import repositories
from tuned.dtos import CreateUserDTO
from tuned.repository.exceptions import NotFound

import logging

logger = logging.getLogger(__name__)
class UserService:
    def __init__(self):
        self._repo = repositories.user

    def login_user(self, credentials: LoginRequestDTO) -> Tuple[bool, Optional[User]]:
        user = self._repo.get_user_by_email(credentials.email)
        if not user or not user.check_password(credentials.password):
            return False, None
            
        login_user(user, remember=credentials.remember)
        
        user.last_login = datetime.now(timezone.utc)
        self._repo.update(user.id, {"last_login": user.last_login}, commit=True)
        return True, user

    def create_user(self, data: CreateUserDTO) -> User:
        try:
            existing = self._repo.get_user_by_email(data.email)
            if existing:
                raise ValueError("Email address already registered.")
        except NotFound:
            pass
        
        created_user = self._repo.create_user(data)
            
        return created_user
    
    def get_user_by_email(self, email) -> User:
        user = self._repo.get_user_by_email(email)
        if user:
            return user
        return None


