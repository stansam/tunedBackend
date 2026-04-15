from tuned.repository.exceptions import AlreadyExists, DatabaseError, InvalidCredentials
from tuned.interface.audit import audit_service
from dataclasses import asdict
from typing import Optional
from datetime import datetime, timezone, timedelta
from flask_login import login_user
from tuned.repository import repositories
from tuned.dtos import CreateUserDTO, LoginRequestDTO, UserResponseDTO, UpdateUserDTO, ActivityLogCreateDTO
from tuned.repository.exceptions import NotFound
from tuned.core.logging import get_logger
from tuned.models import User
from tuned.utils.validators import validate_email, validate_username
from tuned.utils.auth import is_email_verified_required
from tuned.utils.variables import Variables
import logging
import math

logger: logging.Logger = get_logger(__name__)

class UserService:
    def __init__(self):
        self._repo = repositories.user
        self._log_user = audit_service.activity_log
    
    def _check_account_lockout(self, user: User) -> tuple[User, bool, Optional[str]]:
        if user.failed_login_attempts >= 5:
            if user.last_failed_login:
                lockout_duration = timedelta(minutes=15)
                lockout_expires = user.last_failed_login + lockout_duration
                
                if datetime.now(timezone.utc) < lockout_expires:
                    remaining = lockout_expires - datetime.now(timezone.utc)
                    minutes = max(1, math.ceil(remaining.total_seconds() / 60))
                    
                    return user, True, f"Account temporarily locked. Try again in {minutes} minutes."
                else:
                    user.failed_login_attempts = 0
                    user.last_failed_login = None
                    return user, False, None
        
        return user, False, None
    
    def _record_login_attempt(self, user: User, success: bool = True, ip_address: Optional[str] = None) -> User:
        if success:
            user.failed_login_attempts = 0
            user.last_failed_login = None
            user.last_login_at = datetime.now(timezone.utc)
            
            logger.info(f"Successful login for user {user.id} from IP {ip_address}")
            return user
        else:
            user.failed_login_attempts = self._repo.increment_failed_login_attempts(user.id)
            user.last_failed_login = datetime.now(timezone.utc)
            
            logger.warning(
                f"Failed login attempt for user {user.id} from IP {ip_address}. "
                f"Total attempts: {user.failed_login_attempts}"
            )

            return user

    def _log_user_activity(self, before, after, credentials, action):
        audit_dto = ActivityLogCreateDTO(
            user_id=str(after.id),
            action=action,
            entity_type=Variables.USER_ENTITY_TYPE,
            entity_id=str(after.id),
            before=before,
            after=after,
            ip_address=credentials.ip_address,
            user_agent=credentials.user_agent,
            created_by=str(after.id),
        )
        self._log_user.log(audit_dto)

    def login_user(self, credentials: LoginRequestDTO) -> dict:
        try:
            user = self._repo.get_user_by_email(credentials.identifier) if validate_email(credentials.identifier) else None
            if not user:
                success, username = validate_username(credentials.identifier)
                if success:
                    user = self._repo.get_user_by_username(username)
            if not user:
                logger.error(f"User not found.")
                raise InvalidCredentials("Invalid email or username.")
            
            existing_user = user

            if is_email_verified_required():
                if not user.email_verified:
                    logger.info(f'Login blocked — email not verified: {user.email}')
                    raise InvalidCredentials("Email not verified.")
            
            user, is_locked, error_message = self._check_account_lockout(user)
            if is_locked:
                logger.error(f"User account locked.")
                raise InvalidCredentials(error_message)

            if not user.check_password(credentials.password):
                user = self._record_login_attempt(user, False, credentials.ip_address)

                update_user_dto = UpdateUserDTO(
                    user_id=str(user.id),
                    failed_login_attempts=user.failed_login_attempts,
                    last_failed_login=user.last_failed_login,
                )

                updated_user = self._repo.update_user(update_user_dto)

                self._log_user_activity(
                    before=user,
                    after=updated_user,
                    credentials=credentials,
                    action=Variables.USER_LOGIN_ACTION,
                )

                logger.error(f"User with email/username, login failed.")
                raise InvalidCredentials(f"Invalid email/username or password.")
            
            login_user(user, remember=credentials.remember_me)
            
            user = self._record_login_attempt(user, True, credentials.ip_address)
            
            update_user_dto = UpdateUserDTO(
                user_id=str(user.id),
                last_login_at=user.last_login_at,
            )

            user = self._repo.update_user(update_user_dto)
            
            self._log_user_activity(
                    before=existing_user,
                    after=user,
                    credentials=credentials,
                    action=Variables.USER_LOGIN_ACTION,
                )

            user_dto = UserResponseDTO.from_model(user)

            logger.info(f"User login successful.")
            return True, asdict(user_dto)
        except NotFound:
            logger.error(f"User with email/username not found.")
            raise NotFound(f"User with email/username not found.")
        except DatabaseError:
            logger.error(f"Database error while fetching user with email/username.")
            raise DatabaseError(f"Database error while fetching user with email/username.")

    def create_user(self, data: CreateUserDTO) -> dict:
        try:
            # _repo.create_user returns the SQLAlchemy User model instance,
            # which is what flask_login.login_user() requires.
            created_user = self._repo.create_user(data)

            # Establish a session immediately after registration so the user
            # does not need a separate login request.  remember=False means
            # the session cookie will expire at browser close (appropriate for
            # a new registration — the user can choose "remember me" on next login).
            login_user(created_user, remember=False)

            user_dto = UserResponseDTO.from_model(created_user)
            user_dict = asdict(user_dto)

            # Audit the registration event using the shared activity-log helper.
            # This mirrors the pattern used in login_user() above.
            audit_dto = ActivityLogCreateDTO(
                user_id=str(created_user.id),
                action='user_register',
                entity_type=Variables.USER_ENTITY_TYPE,
                entity_id=str(created_user.id),
                before=None,
                after=created_user,
                ip_address=None,  # IP is not available in the interface layer
                user_agent=None,
                created_by=str(created_user.id),
            )
            self._log_user.log(audit_dto)

            logger.info(
                f'User {created_user.email} (id={created_user.id}) '
                f'registered and logged in successfully'
            )
            return user_dict

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


