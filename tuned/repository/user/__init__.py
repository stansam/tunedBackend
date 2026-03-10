from sqlalchemy.orm import Session
from tuned.models import User
from tuned.repository.user.create import CreateUser
from tuned.repository.user.get import GetUserByEmail, GetUserByID, GetAdminUser, GetUsersUser
from tuned.repository.user.exceptions import UserNotFound
from tuned.extensions import db

class UserRepository: 
    def __init__(self):
        self.db = db  
    def create_user(self, user_data: dict) -> User:
        return CreateUser(self.db).execute(user_data)
    def get_user_by_id(self, user_id: string) -> User:
        return GetUserByID(self.db).execute(user_id)
    def get_user_by_email(self, email: string) -> User:
        return GetUserByEmail(self.db).execute(email)
    def get_admin_user(self) -> User:
        return GetAdminUser(self.db).execute()