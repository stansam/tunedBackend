from tuned.models import User
from tuned.dtos import CreateUserDTO
from tuned.manage.data import users_dict
from tuned.interface import Services

def create_users():
    try:
        for user in users_dict:
            service = Services.user
            user_dto = CreateUserDTO(**user)
            user = service.create_user(user_dto)
            print(f"Created user: {user}")
    

    