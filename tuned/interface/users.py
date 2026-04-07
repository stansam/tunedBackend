from tuned.repository.exceptions import AlreadyExists, DatabaseError, InvalidCredentials
from dataclasses import asdict
from datetime import datetime, timezone
from flask_login import login_user
from tuned.repository import repositories
from tuned.dtos import CreateUserDTO, LoginRequestDTO, UserResponseDTO
from tuned.repository.exceptions import NotFound
from tuned.core.logging import get_logger
from tuned.models import User
from tuned.utils.validators import validate_email, validate_username
import logging

logger: logging.Logger = get_logger(__name__)

class UserService:
    def __init__(self):
        self._repo = repositories.user

    def login_user(self, credentials: LoginRequestDTO) -> UserResponseDTO:
        try:
            user = None
            # if credentials.identifier.endswith(".com"):
            # try:
            if validate_email(credentials.identifier):
                user = self._repo.get_user_by_email(credentials.identifier)
            if user is None:
                success, username = validate_username(credentials.identifier)
                if success:
                    user = self._repo.get_user_by_username(username)
            if user is None:
                raise InvalidCredentials("Invalid email or username.")
            # except NotFound:
            #     user = self._repo.get_user_by_username(credentials.identifier)
                
            if not user.check_password(credentials.password):
                logger.error(f"User with email/identifier {credentials.identifier}, login failed.")
                raise InvalidCredentials(f"login failed, password is incorrect.")
            
            login_user(user, remember=credentials.remember_me)
            
            user.last_login = datetime.now(timezone.utc)
            self._repo.update_user(user.id, {"last_login": user.last_login})
            user_dto = UserResponseDTO.from_model(user)
            return True, asdict(user_dto)
        except NotFound:
            logger.error(f"User with email/identifier {credentials.identifier} not found.")
            raise NotFound(f"User with email/identifier {credentials.identifier} not found.")
        except DatabaseError:
            logger.error(f"Database error while fetching user with email/identifier {credentials.identifier}.")
            raise DatabaseError(f"Database error while fetching user with email/identifier {credentials.identifier}.")

    def create_user(self, data: CreateUserDTO) -> UserResponseDTO:
        # try:
        #     existing = self._repo.get_user_by_email(data.email)
        #     if existing:
        #         raise ValueError("Email address already registered.")
        # except NotFound:
        #     pass
        try:
            created_user = self._repo.create_user(data)
            user_dto = UserResponseDTO.from_model(created_user)
            return asdict(user_dto)
        except AlreadyExists:
            logger.error(f"User with email {data.email} already exists.")
            raise AlreadyExists(f"User with email {data.email} already exists.")
        except DatabaseError:
            logger.error(f"Database error while creating user with email {data.email}.")
            raise DatabaseError(f"Database error while creating user with email {data.email}.")
    
    def get_user_by_email(self, email) -> User:
        try:
            user = self._repo.get_user_by_email(email)
            user_dto = UserResponseDTO.from_model(user)
            return asdict(user_dto)
        except NotFound:
            logger.error(f"User with email {email} not found.")
            raise NotFound(f"User with email {email} not found.")
        except DatabaseError:
            logger.error(f"Database error while fetching user with email {email}.")
            raise DatabaseError(f"Database error while fetching user with email {email}.")


