from flask import request, current_app, session
from flask_login import current_user, login_required, logout_user
from flask.views import MethodView
from tuned.interface import user as _interface
from tuned.utils.responses import error_response, success_response, validation_error_response, unauthorized_response
from tuned.utils.auth import (
    check_account_lockout,
    record_login_attempt,
    get_user_ip,
    get_user_by_email_or_username,
)
from tuned.utils.decorators import rate_limit
from tuned.models.audit import ActivityLog
from tuned.core.exceptions import InvalidCredentials, NotFound
from tuned.core.logging import get_logger
from tuned.apis.auth.schemas.login import LoginSchema
from tuned.apis.auth.schemas.registration import RegistrationSchema
from tuned.dtos import UserResponseDTO, LoginRequestDTO, CreateUserDTO
from dataclasses import asdict
from marshmallow import ValidationError
import logging

logger: logging.Logger = get_logger(__name__)

class AuthCheck(MethodView):
    def get(self):
        if current_user.is_authenticated:
            data = UserResponseDTO.from_model(current_user)

            logger.debug(f'User {current_user.email} is authenticated')
            return success_response(asdict(data))
        else:
            logger.debug('User is not authenticated')
            return error_response(
                'User is not authenticated',
                status=401
            )


class Login(MethodView):
    decorators = [rate_limit(max_requests=5, window=60)]

    def post(self):
        try:
            if current_user.is_authenticated:
                logger.debug(f'User {current_user.email} is already authenticated')
                return error_response(
                    'Already authenticated',
                    status=409
                )
            schema = LoginSchema()


            data = request.get_json()
            data = schema.load(data)

        except ValidationError as err:
            logger.error(f'Validation error: {str(err)}')
            return validation_error_response(err.messages)
        
        try:
            dto_data = LoginRequestDTO(**data)
            user_dict = _interface.login_user(dto_data)
            
            logger.info(f'User {user_dict.get("email")} logged in successfully')
            return success_response(user_dict)

        except NotFound:
            return error_response('Invalid credentials', status=401)
        except InvalidCredentials as e:
            return unauthorized_response("Invalid credentials")
            
        except Exception as e:
            logger.error(f"Login error for {data.get('identifier', 'Unknown')}: {str(e)}")
            return error_response('Login failed. Please try again.', status=500)

class Logout(MethodView):
    decorators = [login_required]

    def post(self):
        try:
            user_id = current_user.id if current_user.is_authenticated else None
            ip = get_user_ip()

            logout_user()
            session.clear()

            # resp_tuple = success_response('Logged out successfully')
            # resp = resp_tuple[0]
            
            # resp.delete_cookie(
            #     current_app.config.get('SESSION_COOKIE_NAME', 'tuned_session'),
            #     path=current_app.config.get('SESSION_COOKIE_PATH', '/'),
            #     domain=current_app.config.get('SESSION_COOKIE_DOMAIN'),
            #     samesite=current_app.config.get('SESSION_COOKIE_SAMESITE', 'None')
            # )
            logger.info(f'User {user_id} logged out successfully.')
            return success_response('Logged out successfully')

        except Exception as e:
            logger.error(f'Logout error: {str(e)}')
            return error_response('Logout failed', status=500)

class Register(MethodView):
    def post(self):
        try:
            if current_user.is_authenticated:
                logger.debug(f'User {current_user.email} is already authenticated')
                return error_response(
                    'Already authenticated',
                    status=409
                )
            schema = RegistrationSchema()
            data = request.get_json()
            data = schema.load(data)
            
        except ValidationError as err:
            logger.error(f'Validation error: {str(err)}')
            return validation_error_response(err.messages)
        
        try:
            user_dto = CreateUserDTO(**data)
            user_dict = _interface.create_user(user_dto)
            
            # ActivityLog.log(
            #     action='user_register',
            #     user_id=user_dict.get('id'),
            #     entity_type='User',
            #     entity_id=user_dict.get('id'),
            #     description=f'User {user_dict.get("email")} registered successfully',
            #     ip_address=get_user_ip(),
            #     user_agent=request.headers.get('User-Agent'),
            # )
            logger.info(f'User {user_dict.get("email")} registered successfully')
            return success_response(user_dict)
        except Exception as e:
            logger.error(f'Registration error: {str(e)}')
            return error_response('Registration failed', status=500)