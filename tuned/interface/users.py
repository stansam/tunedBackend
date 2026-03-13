from typing import Tuple, Optional
from datetime import datetime, timezone, timedelta
from flask_login import login_user
from tuned.models.user import User
from tuned.repository import Repository
from tuned.dtos import CreateUserDTO
import logging

logger = logging.getLogger(__name__)
class UserService:
    def __init__(self):
        self.user_repo = Repository.user

    def login_user(self, credentials: LoginRequestDTO) -> Tuple[bool, Optional[User]]:
        user = self.user_repo.get_user_by_email(credentials.email)
        if not user or not user.check_password(credentials.password):
            return False, None
            
        login_user(user, remember=credentials.remember)
        
        user.last_login = datetime.now(timezone.utc)
        self.user_repo.update(user.id, {"last_login": user.last_login}, commit=True)
        return True, user

    def create_user(self, data: CreateUserDTO) -> User:
        existing = self.user_repo.get_user_by_email(data.email)
        if existing:
            raise ValueError("Email address already registered.")
        
        created_user = self.user_repo.create_user(data)
            
        return created_user
    
    def get_user_by_email(self, email) -> User:
        user = self.user_repo.get_user_by_email(email)
        if user:
            return user
        return None


