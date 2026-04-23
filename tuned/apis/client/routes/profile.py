from flask import request, current_app, session, make_response
from flask_login import current_user, login_required
from flask.views import MethodView
from tuned.interface import user as _interface
from tuned.utils.responses import error_response, success_response, validation_error_response
from tuned.utils.auth import get_user_ip, get_user_agent
from tuned.core.exceptions import InvalidCredentials, NotFound
from tuned.apis.client.schemas.profile import UpdateProfileSchema, ChangePasswordSchema
from tuned.dtos.user import UpdateProfileRequestDTO, ChangePasswordRequestDTO, EmailVerificationResendDTO
from tuned.dtos.base import BaseRequestDTO
from marshmallow import ValidationError
import logging

logger: logging.Logger = logging.getLogger(__name__)

class ProfileView(MethodView):
    decorators = [login_required]

    def get(self):
        try:
            profile_data = _interface.get_profile(current_user.id)
            return success_response(profile_data)
        except Exception as e:
            logger.error(f'Get profile error: {str(e)}')
            return error_response('Failed to fetch profile', status=500)

    def patch(self):
        try:
            schema = UpdateProfileSchema()
            data = schema.load(request.get_json())
        except ValidationError as err:
            return validation_error_response(err.messages)

        try:
            dto_data = UpdateProfileRequestDTO(**data)
            locale = BaseRequestDTO(ip_address=get_user_ip(), user_agent=get_user_agent())
            profile_data = _interface.update_profile(current_user.id, dto_data, locale)
            return success_response(profile_data)
        except Exception as e:
            logger.error(f'Update profile error: {str(e)}')
            return error_response('Failed to update profile', status=500)

class AvatarUploadView(MethodView):
    decorators = [login_required]

    def post(self):
        if 'file' not in request.files:
            return error_response('No file uploaded', status=400)
            
        file = request.files['file']
        if file.filename == '':
            return error_response('No file selected', status=400)

        if not file.content_type.startswith('image/'):
            return error_response('Only images are allowed', status=400)

        try:
            locale = BaseRequestDTO(ip_address=get_user_ip(), user_agent=get_user_agent())
            result = _interface.upload_avatar(current_user.id, file, locale)
            return success_response(result)
        except Exception as e:
            logger.error(f'Avatar upload error: {str(e)}')
            return error_response('Failed to upload avatar', status=500)

    def delete(self):
        try:
            locale = BaseRequestDTO(ip_address=get_user_ip(), user_agent=get_user_agent())
            result = _interface.delete_avatar(current_user.id, locale)
            return success_response(result)
        except Exception as e:
            logger.error(f'Avatar delete error: {str(e)}')
            return error_response('Failed to delete avatar', status=500)

class VerifyEmailView(MethodView):
    decorators = [login_required]

    def post(self):
        try:
            dto = EmailVerificationResendDTO(
                email=current_user.email,
                ip_address=get_user_ip(),
                user_agent=get_user_agent()
            )
            _interface.resend_verification_email(dto)
            return success_response({"success": True})
        except ValueError as e:
            if str(e).startswith('rate_limited'):
                return error_response('Please wait before resending', status=429)
            return error_response(str(e), status=400)
        except Exception as e:
            logger.error(f'Resend verification error: {str(e)}')
            return error_response('Failed to resend verification', status=500)

class ChangePasswordView(MethodView):
    decorators = [login_required]

    def post(self):
        try:
            schema = ChangePasswordSchema()
            data = schema.load(request.get_json())
        except ValidationError as err:
            return validation_error_response(err.messages)

        try:
            dto_data = ChangePasswordRequestDTO(
                current_password=data['current_password'],
                new_password=data['new_password']
            )
            locale = BaseRequestDTO(ip_address=get_user_ip(), user_agent=get_user_agent())
            _interface.change_password(current_user.id, dto_data, locale)
            return success_response({"success": True})
        except InvalidCredentials:
            return error_response("Invalid current password", status=400)
        except Exception as e:
            logger.error(f'Change password error: {str(e)}')
            return error_response('Failed to change password', status=500)
