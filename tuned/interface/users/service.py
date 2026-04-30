from typing import Optional, TYPE_CHECKING, Any, Tuple
from datetime import datetime, timezone
import logging
import os
import uuid
from flask_login import login_user
from flask import current_app
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from dataclasses import asdict

from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound, InvalidCredentials
from tuned.dtos import (
    CreateUserDTO, LoginRequestDTO, UserResponseDTO, UpdateUserDTO,
    ActivityLogCreateDTO, EmailVerificationResendDTO, EmailVerifyConfirmDTO,
    ProfileResponseDTO, UpdateProfileRequestDTO, ChangePasswordRequestDTO
)
from tuned.dtos.base import BaseRequestDTO
from tuned.core.events import get_event_bus
from tuned.core.logging import get_logger
from tuned.utils.variables import Variables
from tuned.utils.auth import is_email_verified_required
from tuned.services.users import UserService as CoreUserService
from tuned.redis_client import redis_client

if TYPE_CHECKING:
    from tuned.repository import Repository

logger: logging.Logger = get_logger(__name__)
event_bus = get_event_bus()

class UserService:
    def __init__(self, repos: Optional["Repository"] = None):
        if repos:
            self._repo = repos.user
            from tuned.interface.audit import AuditService
            self._audit = AuditService(repos=repos)
            self._core = CoreUserService(
                user_repo=repos.user,
                audit_service=self._audit.activity_log
            )
        else:
            # Fallback for legacy
            from tuned.repository import repositories
            self._repo = repositories.user
            from tuned.interface.audit import AuditService
            self._audit = AuditService(repos=repositories)
            self._core = CoreUserService(
                user_repo=repositories.user,
                audit_service=self._audit.activity_log
            )

    def login_user(self, credentials: LoginRequestDTO) -> Tuple[bool, dict[str, Any]]:
        try:
            user = self._core.authenticate_user(credentials)
            
            if is_email_verified_required() and not user.email_verified:
                logger.info(f'Login blocked — email not verified: {user.email}')
                raise InvalidCredentials("Email not verified.")

            # Framework specific side effect
            login_user(user, remember=credentials.remember_me)
            
            user_dto = UserResponseDTO.from_model(user)
            return True, asdict(user_dto)
        except InvalidCredentials as e:
            logger.error(f"Login failed: {e}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected login error: {e}")
            raise DatabaseError(str(e))

    def create_user(self, data: CreateUserDTO, locale: BaseRequestDTO, referred_by_code: Optional[str] = None) -> dict[str, Any]:
        try:
            created_user = self._core.register_user(
                data, 
                locale.ip_address or "unknown", 
                locale.user_agent or "unknown"
            )
            
            try:
                _user, raw_token = self._repo.generate_verification_token(str(created_user.id))
                event_bus.emit('user.registered', {
                    'user_id': created_user.id,
                    'raw_token': raw_token,
                    'email': created_user.email,
                    'name': created_user.get_name()
                })

                if referred_by_code is not None:
                    event_bus.emit('user.registered_with_referral', {
                        'new_user_id': str(created_user.id),
                        'referral_code': referred_by_code
                    })
            except Exception as token_exc:
                logger.error(f'[create_user] Token/email step failed for user {created_user.id}: {token_exc!r}')

            return {'email': created_user.email}
        except AlreadyExists as e:
            raise e
        except Exception as e:
            raise DatabaseError(str(e))

    def resend_verification_email(self, dto: EmailVerificationResendDTO) -> bool:
        cooldown_key = f'email_resend_cooldown:{dto.email}'
        if redis_client.exists(cooldown_key):
            ttl: int = redis_client.ttl(cooldown_key)
            raise ValueError(f'rate_limited:{ttl}')

        user = self._repo.get_user_for_resend(dto.email)
        if user is None or user.email_verified:
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
        return True

    def confirm_email_verification(self, dto: EmailVerifyConfirmDTO) -> Tuple[bool, str]:
        try:
            verified_user = self._repo.confirm_email_verification(dto.uid, dto.token)
            
            # Audit log
            # Audit log
            self._audit.activity_log.log(ActivityLogCreateDTO(
                user_id=str(verified_user.id),
                action=Variables.EMAIL_VERIFICATION_ACTION,
                entity_type=Variables.USER_ENTITY_TYPE,
                entity_id=str(verified_user.id),
                before=None,
                after=asdict(verified_user) if hasattr(verified_user, "__dict__") else str(verified_user),
                ip_address=dto.ip_address,
                user_agent=dto.user_agent,
                created_by=str(verified_user.id),
            ))
            self._repo.save()

            event_bus.emit('user.email_verified', {'user_id': verified_user.id})
            return True, Variables.OK
        except (NotFound, AlreadyExists) as e:
            return False, str(e)
        except ValueError as e:
            return False, str(e)

    def get_profile(self, user_id: str) -> dict[str, Any]:
        user = self._repo.get_user_by_id(user_id)
        return asdict(ProfileResponseDTO.from_model(user))

    def update_profile(self, user_id: str, data: UpdateProfileRequestDTO, locale: BaseRequestDTO) -> dict[str, Any]:
        user = self._repo.get_user_by_id(user_id)
        update_dto = UpdateUserDTO(
            user_id=user_id,
            first_name=data.first_name,
            last_name=data.last_name,
            phone_number=data.phone_number,
            gender=data.gender
        )
        updated_user = self._repo.update_user(update_dto, actor_id=user_id)
        
        # Log activity
        # Log activity
        self._audit.activity_log.log(ActivityLogCreateDTO(
            user_id=user_id,
            action='USER_PROFILE_UPDATE',
            entity_type=Variables.USER_ENTITY_TYPE,
            entity_id=user_id,
            before=asdict(user) if hasattr(user, "__dict__") else str(user),
            after=asdict(updated_user) if hasattr(updated_user, "__dict__") else str(updated_user),
            ip_address=locale.ip_address,
            user_agent=locale.user_agent,
            created_by=user_id
        ))
        self._repo.save()
        return asdict(ProfileResponseDTO.from_model(updated_user))

    def change_password(self, user_id: str, data: ChangePasswordRequestDTO, locale: BaseRequestDTO) -> bool:
        user = self._repo.get_user_by_id(user_id)
        if not user.check_password(data.current_password):
            raise InvalidCredentials("Invalid current password.")
            
        new_hash = generate_password_hash(data.new_password)
        updated_user = self._repo.update_user(
            UpdateUserDTO(user_id=user_id, password_hash=new_hash),
            actor_id=user_id
        )
        
        self._audit.activity_log.log(ActivityLogCreateDTO(
            user_id=user_id,
            action='PASSWORD_CHANGE',
            entity_type=Variables.USER_ENTITY_TYPE,
            entity_id=user_id,
            before=None,
            after=None,
            ip_address=locale.ip_address,
            user_agent=locale.user_agent,
            created_by=user_id
        ))
        self._repo.save()
        return True

    def upload_avatar(self, user_id: str, file: Any, locale: BaseRequestDTO) -> dict[str, Any]:
        user = self._repo.get_user_by_id(user_id)
        
        static_folder = current_app.static_folder or "static"
        upload_folder = os.path.join(static_folder, 'client/assets/profile_pics')
        os.makedirs(upload_folder, exist_ok=True)
        
        original_filename = getattr(file, "filename", "avatar.png") or "avatar.png"
        filename = secure_filename(original_filename)
        ext = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        updated_user = self._repo.update_user(
            UpdateUserDTO(user_id=user_id, profile_pic=unique_filename),
            actor_id=user_id
        )
        
        self._audit.activity_log.log(ActivityLogCreateDTO(
            user_id=user_id,
            action='AVATAR_UPLOAD',
            entity_type=Variables.USER_ENTITY_TYPE,
            entity_id=user_id,
            before=None,
            after=None,
            ip_address=locale.ip_address,
            user_agent=locale.user_agent,
            created_by=user_id
        ))
        self._repo.save()
        return {"profile_pic_url": updated_user.get_profile_pic_url()}

    def delete_avatar(self, user_id: str, locale: BaseRequestDTO) -> dict[str, Any]:
        user = self._repo.get_user_by_id(user_id)
        updated_user = self._repo.update_user(
            UpdateUserDTO(user_id=user_id, profile_pic="default.png"),
            actor_id=user_id
        )
        self._audit.activity_log.log(ActivityLogCreateDTO(
            user_id=user_id,
            action='AVATAR_DELETE',
            entity_type=Variables.USER_ENTITY_TYPE,
            entity_id=user_id,
            before=None,
            after=None,
            ip_address=locale.ip_address,
            user_agent=locale.user_agent,
            created_by=user_id
        ))
        self._repo.save()
        return {"profile_pic_url": updated_user.get_profile_pic_url()}
