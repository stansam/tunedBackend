from sqlalchemy.orm import Session
from tuned.models import User
from tuned.repository.user.create import CreateUser
from tuned.repository.user.get import GetUserByEmail, GetUserByID, GetAdminUser, GetUserByUsername
from tuned.repository.user.update import UpdateUser
from tuned.repository.user.exceptions import UserNotFound
from tuned.extensions import db

class UserRepository: 
    def __init__(self):
        self.db = db  
    def create_user(self, user_data: dict) -> User:
        return CreateUser(self.db.session).execute(user_data)
    def get_user_by_id(self, user_id: string) -> User:
        return GetUserByID(self.db.session).execute(user_id)
    def get_user_by_email(self, email: string) -> User:
        return GetUserByEmail(self.db.session).execute(email)
    def get_user_by_username(self, username: string) -> User:
        return GetUserByUsername(self.db.session).execute(username)
    def get_admin_user(self) -> User:
        return GetAdminUser(self.db.session).execute()
    def update_user(self, user_id: string, updates: dict) -> User:
        return UpdateUser(self.db.session).execute(user_id, updates)