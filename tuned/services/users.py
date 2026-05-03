from __future__ import annotations
import logging
from typing import Optional, TYPE_CHECKING, Tuple, Any, cast, Dict
from datetime import datetime, timezone, timedelta
import math
from dataclasses import asdict

from tuned.core.exceptions import InvalidCredentials, ServiceError
from tuned.repository.protocols import UserRepositoryProtocol
from tuned.dtos import (
    CreateUserDTO, LoginRequestDTO, UserResponseDTO, UpdateUserDTO,
    ActivityLogCreateDTO
)
from tuned.core.logging import get_logger
from tuned.utils.validators import validate_email, validate_username
from tuned.utils.variables import Variables

if TYPE_CHECKING:
    from tuned.interface.protocols import ActivityLogServiceProtocol
    from tuned.models import User

logger: logging.Logger = get_logger(__name__)

class UserService:
    def __init__(
        self, 
        user_repo: UserRepositoryProtocol,
        audit_service: ActivityLogServiceProtocol
    ):
        self._repo = user_repo
        self._audit_service = audit_service
    
    def check_new_user_referral(self, referrer_code: Optional[str]) -> bool:
        try:
            if not referrer_code:
                return False
            referrer = self._repo.get_by_referral_code(referrer_code)
            if not referrer:
                raise InvalidCredentials("Referral code is invalid")
            return True
        except InvalidCredentials as e:
            raise e
        except Exception as e:
            raise ServiceError(f"Error while fetching user by referral code: {str(e)}") from e

    def _check_account_lockout(self, user: User) -> Tuple[User, bool, Optional[str]]:
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

    def authenticate_user(self, credentials: LoginRequestDTO) -> User:
        user = self._repo.get_user_by_email(credentials.identifier) if validate_email(credentials.identifier) else None
        if not user:
            success, username = validate_username(credentials.identifier)
            if success and username: # Ensure username is not None
                user = self._repo.get_user_by_username(username)
        
        if not user:
            raise InvalidCredentials("Invalid email or username.")

        user, is_locked, error_message = self._check_account_lockout(user)
        if is_locked:
            raise InvalidCredentials(error_message or "Account locked")

        if not user.check_password(credentials.password):
            failed_attempts = self._repo.increment_failed_login_attempts(user.id)
            user.failed_login_attempts = failed_attempts
            user.last_failed_login = datetime.now(timezone.utc)
            
            self._log_activity(
                user_id=str(user.id),
                action=Variables.USER_LOGIN_ACTION,
                before=None,
                after=user,
                ip_address=credentials.ip_address,
                user_agent=credentials.user_agent
            )
            self._repo.save()
            raise InvalidCredentials("Invalid password.")

        user.failed_login_attempts = 0
        user.last_failed_login = None
        user.last_login_at = datetime.now(timezone.utc)
        
        updated_user = self._repo.update_user(
            UpdateUserDTO(
                user_id=str(user.id),
                last_login_at=user.last_login_at,
                failed_login_attempts=0,
                last_failed_login=None
            ),
            actor_id=str(user.id)
        )
        
        self._log_activity(
            user_id=str(user.id),
            action=Variables.USER_LOGIN_ACTION,
            before=user,
            after=updated_user,
            ip_address=credentials.ip_address,
            user_agent=credentials.user_agent
        )
        self._repo.save()
        return updated_user

    def _log_activity(self, user_id: str, action: str, before: Optional[User], after: Optional[User], ip_address: Optional[str], user_agent: Optional[str]) -> None:
        try:
            def _serialize(obj: Optional[User]) -> Optional[Dict[str, Any]]:
                if obj is None:
                    return None
                return asdict(UserResponseDTO.from_model(obj))

            self._audit_service.log(ActivityLogCreateDTO(
                user_id=user_id,
                action=action,
                entity_type=Variables.USER_ENTITY_TYPE,
                entity_id=user_id,
                before=_serialize(before),
                after=_serialize(after),
                ip_address=ip_address or "unknown",
                user_agent=user_agent or "unknown",
                created_by=user_id
            ))
        except Exception as e:
            logger.error(f"Failed to log user activity: {e}")

    def register_user(self, data: CreateUserDTO, ip_address: str, user_agent: str) -> User:
        user = self._repo.create_user(data)
        
        self._log_activity(
            user_id=str(user.id),
            action=Variables.USER_REGISTER_ACTION,
            before=None,
            after=user,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self._repo.save()
        return user