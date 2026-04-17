from tuned.dtos.base import BaseRequestDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, InvalidCredentials
from tuned.interface.audit import audit_service
from tuned.redis_client import redis_client
# removed synchronous email import to enforce decoupled architecture via celery Queue
from dataclasses import asdict
from typing import Optional
from datetime import datetime, timezone, timedelta
from flask_login import login_user
from tuned.repository import repositories
from tuned.dtos import (
    CreateUserDTO, LoginRequestDTO, UserResponseDTO, UpdateUserDTO,
    ActivityLogCreateDTO, EmailVerificationResendDTO, EmailVerifyConfirmDTO,
)
from tuned.core.events import get_event_bus
from tuned.repository.exceptions import NotFound, AlreadyExists
from tuned.core.logging import get_logger
from tuned.models import User
from tuned.utils.validators import validate_email, validate_username
from tuned.utils.auth import is_email_verified_required
from tuned.utils.variables import Variables
import logging
import math

logger: logging.Logger = get_logger(__name__)
event_bus = get_event_bus()
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
        try:
            self._log_user.log(audit_dto)
        except Exception as exc:
            logger.error(f"[audit] Failed to log user activity for {after.id}: {exc!r}")

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

    def create_user(self, data: CreateUserDTO, locale: BaseRequestDTO ) -> dict:
        try:

            created_user = self._repo.create_user(data)

            audit_dto = ActivityLogCreateDTO(
                user_id=str(created_user.id),
                action=Variables.USER_REGISTER_ACTION,
                entity_type=Variables.USER_ENTITY_TYPE,
                entity_id=str(created_user.id),
                before=None,
                after=created_user,
                ip_address=locale.ip_address,
                user_agent=locale.user_agent,
                created_by=str(created_user.id),
            )
            self._log_user.log(audit_dto)
            try:
                _user, raw_token = self._repo.generate_verification_token(str(created_user.id))
                event_bus.emit('user.registered', {
                    'user_id': created_user.id,
                    'raw_token': raw_token,
                    'email': created_user.email,
                    'name': created_user.get_name()
                })
            except Exception as token_exc:
                logger.error(
                    f'[create_user] Token/email step failed for user {created_user.id}: {token_exc!r}'
                )

            logger.info(
                f'User {created_user.email} (id={created_user.id}) registered — '
                f'verification email dispatched'
            )
            return {'email': created_user.email}

        except AlreadyExists:
            logger.error(f"User with email {data.email} already exists.")
            raise AlreadyExists(f"User with email {data.email} already exists.")
        except DatabaseError:
            logger.error(f"Database error while creating user with email {data.email}.")
            raise DatabaseError(f"Database error while creating user with email {data.email}.")

    def resend_verification_email(self, dto: EmailVerificationResendDTO) -> bool:
        cooldown_key = f'email_resend_cooldown:{dto.email}'
        if redis_client.exists(cooldown_key):
            ttl: int = redis_client.ttl(cooldown_key)
            raise ValueError(f'rate_limited:{ttl}')

        user: User | None = self._repo.get_user_for_resend(dto.email)
        if user is None:
            redis_client.setex(cooldown_key, 60, '1')
            return True

        if user.email_verified:
            return True

        try:
            _user, raw_token = self._repo.generate_verification_token(str(user.id))
            event_bus.emit('user.resend_verification_email', {
                'user_id': _user.id,
                'raw_token': raw_token,
                'email': _user.email,
                'name': _user.get_name()
            })
        except AlreadyExists:
            return True
        except Exception as exc:
            logger.error(f'[resend] Token/email error for {dto.email}: {exc!r}')
            redis_client.setex(cooldown_key, 60, '1')
            raise

        redis_client.setex(cooldown_key, 60, '1')
        logger.info(f'[resend] Verification email re-queued for {dto.email}')
        return True

    def confirm_email_verification(self, dto: EmailVerifyConfirmDTO) -> tuple[bool, str]:
        try:
            verified_user = self._repo.confirm_email_verification(dto.uid, dto.token)

            audit_dto = ActivityLogCreateDTO(
                user_id=str(verified_user.id),
                action=Variables.EMAIL_VERIFICATION_ACTION,
                entity_type=Variables.USER_ENTITY_TYPE,
                entity_id=str(verified_user.id),
                before=None,
                after=verified_user,
                ip_address=dto.ip_address,
                user_agent=dto.user_agent,
                created_by=str(verified_user.id),
            )
            try:
                self._log_user.log(audit_dto)
            except Exception as audit_exc:
                logger.error(f"[audit] Failed to log email verification for {verified_user.id}: {audit_exc!r}")

            try:
                event_bus.emit('user.email_verified', {
                    'user_id': verified_user.id
                })
            except Exception as event_exc:
                logger.error(f"[events] Failed to emit user.email_verified for {verified_user.id}: {event_exc!r}")

            logger.info(f'Email verified for user {verified_user.id}')
            return True, Variables.OK

        except NotFound:
            return False, Variables.NOT_FOUND
        except AlreadyExists:
            return False, Variables.ALREADY_VERIFIED
        except ValueError as exc:
            reason = str(exc)  # 'expired', 'invalid', 'no_token'
            return False, reason
        except DatabaseError as exc:
            logger.error(f'[confirm] DB error for uid {dto.uid}: {exc!r}')
            raise

    
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


