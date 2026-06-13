from __future__ import annotations
from typing import Optional, TYPE_CHECKING, Any, Tuple, Dict, cast
from datetime import datetime, timezone
import logging
import os
import uuid
from flask_login import login_user
from flask import current_app
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from dataclasses import asdict

from tuned.core.exceptions import AlreadyExists, DatabaseError, NotFound, InvalidCredentials, ServiceError
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
from tuned.interface.audit import AuditService

if TYPE_CHECKING:
    from tuned.repository import Repository
    from tuned.interface import Services 
    from tuned.models import User

logger: logging.Logger = get_logger(__name__)
event_bus = get_event_bus()

class UserService:
    def __init__(self, repos: Repository, interfaces: Services):
        self._repo = repos.user
        self._audit = AuditService(repos=repos)
        self._core = CoreUserService(
            user_repo=repos.user,
            audit_service=self._audit.activity_log
        )
        self._interfaces = interfaces

    def login_user(self, credentials: LoginRequestDTO) -> Tuple[bool, Dict[str, Any]]:
        try:
            user = self._core.authenticate_user(credentials)
            
            # if is_email_verified_required() and not user.email_verified:
            #     logger.info(f'Login blocked — email not verified: {user.email}')
            #     raise InvalidCredentials("Email not verified.")

            login_user(user, remember=credentials.remember_me)
            
            user_dto = UserResponseDTO.from_model(user)
            return True, asdict(user_dto)
        except InvalidCredentials as e:
            logger.error(f"Login failed: {e}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected login error: {e}")
            raise DatabaseError(str(e))

    def create_user(self, data: CreateUserDTO, locale: BaseRequestDTO, referred_by_code: Optional[str] = None) -> Dict[str, Any]:
        try:
            created_user, raw_token = self._core.register_user(
                data, 
                locale.ip_address or "unknown", 
                locale.user_agent or "unknown"
            )
            
            try:
                if raw_token is not None:
                    event_bus.emit('user.registered', {
                        'user_id': created_user.id,
                        'raw_token': raw_token,
                        'email': created_user.email,
                        'name': created_user.get_name(),
                        'ip_address': locale.ip_address or "unknown"
                    })

                if referred_by_code is not None:
                    event_bus.emit('user.registered_with_referral', {
                        'new_user_id': str(created_user.id),
                        'referral_code': referred_by_code
                    })
            except Exception as token_exc:
                logger.error(f'[create_user] Token/email step failed for user {created_user.id}: {token_exc!r}')
                raise

            return {'email': created_user.email}
        except AlreadyExists as e:
            raise e
        except ServiceError as e:
            raise e
        except Exception as e:
            raise DatabaseError(str(e))


    def resend_verification_email(self, dto: EmailVerificationResendDTO) -> bool:
        cooldown_key = f'email_resend_cooldown:{dto.email}'
        if redis_client.exists(cooldown_key):
            ttl: int = int(cast(Any, redis_client.ttl(cooldown_key)))
            logger.warning(f"[resend] Token/email error for {dto.email}: rate limited {ttl}s")
            raise ValueError(f'rate_limited:{ttl}')

        user = self._repo.get_user_for_resend(dto.email)
        if user is None or user.email_verified:
            logger.warning(f"[resend] Token/email error for {dto.email}: user not found or email already verified")
            return True

        try:
            _user, raw_token = self._repo.generate_verification_token(str(user.id))
            event_bus.emit('user.resend_verification_email', {
                'user_id': _user.id,
                'raw_token': raw_token,
                'email': _user.email,
                'name': _user.get_name()
            })
        except AlreadyExists as exc:
            logger.error(f"[resend] AlreadyExists error for {dto.email}: {exc!r}")
            return True
        except Exception as exc:
            logger.error(f"[resend] Token/email error for {dto.email}: {exc!r}")
            redis_client.setex(cooldown_key, 60, '1')
            raise

        redis_client.setex(cooldown_key, 60, '1')
        return True

    def confirm_email_verification(self, dto: EmailVerifyConfirmDTO) -> Tuple[bool, str]:
        try:
            verified_user = self._repo.confirm_email_verification(dto.uid, dto.token)
            
            self._audit.activity_log.log(ActivityLogCreateDTO(
                user_id=str(verified_user.id),
                action=Variables.EMAIL_VERIFICATION_ACTION,
                entity_type=Variables.USER_ENTITY_TYPE,
                entity_id=str(verified_user.id),
                before=None,
                after=asdict(UserResponseDTO.from_model(verified_user)),
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

    def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        try:
            user = self._repo.get_user_by_id(user_id)
            return asdict(UserResponseDTO.from_model(user))
        except Exception as e:
            logger.error(f"Error fetching user by id {user_id}: {str(e)}")
            raise
    
    def get_user_obj(self, user_id: str) -> User:
        try:
            return self._repo.get_user_by_id(user_id)
        except Exception as e:
            logger.error(f"Error fetching user by id {user_id}: {str(e)}")
            raise

    def get_user_by_email(self, email: str) -> Dict[str, Any]:
        user = self._repo.get_user_for_resend(email)
        if not user:
            raise NotFound("User not found")
        return asdict(UserResponseDTO.from_model(user))

    def get_profile(self, user_id: str) -> Dict[str, Any]:
        user = self._repo.get_user_by_id(user_id)
        return asdict(ProfileResponseDTO.from_model(user))

    def update_profile(self, user_id: str, data: UpdateProfileRequestDTO, locale: BaseRequestDTO) -> Dict[str, Any]:
        user = self._repo.get_user_by_id(user_id)
        before_snapshot = asdict(UserResponseDTO.from_model(user))

        update_dto = UpdateUserDTO(
            user_id=user_id,
            first_name=data.first_name,
            last_name=data.last_name,
            phone_number=data.phone_number,
            gender=data.gender
        )
        updated_user = self._repo.update_user(update_dto, actor_id=user_id)
        after_snapshot = asdict(UserResponseDTO.from_model(updated_user))
        
        self._audit.activity_log.log(ActivityLogCreateDTO(
            user_id=user_id,
            action=Variables.PROFILE_UPDATE_ACTION,
            entity_type=Variables.USER_ENTITY_TYPE,
            entity_id=user_id,
            before=before_snapshot,
            after=after_snapshot,
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
        _ = self._repo.update_user(
            UpdateUserDTO(user_id=user_id, password_hash=new_hash),
            actor_id=user_id
        )
        
        self._audit.activity_log.log(ActivityLogCreateDTO(
            user_id=user_id,
            action=Variables.PASSWORD_CHANGE_ACTION,
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

    def upload_avatar(self, user_id: str, file: Any, locale: BaseRequestDTO) -> Dict[str, Any]:
        user = self._repo.get_user_by_id(user_id)
        
        old_profile_pic_id = user.profile_pic_id
        
        from tuned.models.enums import AssetOwnerType
        media_dto = self._interfaces.media.upload_file(
            file=file,
            owner_type=AssetOwnerType.USER,
            owner_id=user_id,
            is_public=True
        )
        
        user.profile_pic_id = uuid.UUID(media_dto.id)
        
        self._audit.activity_log.log(ActivityLogCreateDTO(
            user_id=user_id,
            action=Variables.AVATAR_UPLOAD_ACTION,
            entity_type=Variables.USER_ENTITY_TYPE,
            entity_id=user_id,
            before=None,
            after=None,
            ip_address=locale.ip_address,
            user_agent=locale.user_agent,
            created_by=user_id
        ))
        self._repo.save()

        if old_profile_pic_id and user.profile_pic_id != old_profile_pic_id:
            try:
                self._interfaces.media.delete_media(str(old_profile_pic_id))
                self._repo.save()
            except Exception as del_exc:
                logger.error("[UserService.upload_avatar] Failed to delete old avatar: %r", del_exc)

        return {"profile_pic_url": user.get_profile_pic_url()}

    def delete_avatar(self, user_id: str, locale: BaseRequestDTO) -> Dict[str, Any]:
        user = self._repo.get_user_by_id(user_id)
        
        if user.profile_pic_id:
            try:
                self._interfaces.media.delete_media(str(user.profile_pic_id))
            except Exception as del_exc:
                logger.error("[UserService.delete_avatar] Failed to delete old avatar: %r", del_exc)
                raise del_exc
                
        user.profile_pic_id = None
        
        self._audit.activity_log.log(ActivityLogCreateDTO(
            user_id=user_id,
            action=Variables.AVATAR_DELETE_ACTION,
            entity_type=Variables.USER_ENTITY_TYPE,
            entity_id=user_id,
            before=None,
            after=None,
            ip_address=locale.ip_address,
            user_agent=locale.user_agent,
            created_by=user_id
        ))
        self._repo.save()
        return {"profile_pic_url": user.get_profile_pic_url()}
