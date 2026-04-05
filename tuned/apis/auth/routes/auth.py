from datetime import timezone, datetime
from flask import request
from flask_login import current_user
from flask.views import MethodView
from tuned.interface import user as _interface
from tuned.utils.responses import error_response, success_response, validation_error_response
from tuned.core.exceptions import InvalidCredentials, NotFound
from tuned.core.logging import get_logger
from tuned.apis.auth.schemas.login import LoginSchema
from tuned.dtos import UserResponseDTO, LoginRequestDTO 
from dataclasses import asdict
from marshmallow import ValidationError
# import json
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
    def post(self):
        try:
            schema = LoginSchema()

            data = None
            if request.args:
                data = schema.loads(request.args)

        except ValidationError as err:
            logger.error(f'Validation error: {str(err)}')
            return validation_error_response(err.messages)
        
        try:
            data = LoginRequestDTO(**data)
            user = _interface.login_user(data)
            user_dto = UserResponseDTO.from_model(user)
            return success_response(asdict(user_dto))
        except NotFound:
            logger.error(f'User with email {data.email} not found.')
            return error_response(
                'User not found',
                status=404
            )
        except InvalidCredentials:
            logger.error(f'login failed for {data.email} invalid credentials.')
            return error_response(
                'Invalid credentials',
                status=401
            )
        except Exception as e:
            logger.error(f'login failed for {data.email}.')
            return error_response(
                'login failed for {data.email}, try again.',
                status=500
            )