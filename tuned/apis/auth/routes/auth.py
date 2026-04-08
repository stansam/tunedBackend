from flask import request, current_app, session
from flask_login import current_user, login_required, logout_user
from flask.views import MethodView
from tuned.interface import user as _interface
from tuned.utils.responses import error_response, success_response, validation_error_response
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
from tuned.dtos import UserResponseDTO, LoginRequestDTO 
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
            # if request.args:
            #     data = schema.loads(request.args)

        except ValidationError as err:
            logger.error(f'Validation error: {str(err)}')
            return validation_error_response(err.messages)
        
        try:
            # ── Pre-validation ─────────────────────────────────────
            # Fetch user context for security checks before hitting 
            # the business interface or computing bcrypt hashes.
            pre_user = get_user_by_email_or_username(data['identifier'])

            if not pre_user:
                return error_response('Invalid credentials', status=401)

            is_locked, lock_message = check_account_lockout(pre_user)
            if is_locked:
                logger.warning(f'Login attempt on locked account: {pre_user.id}')
                return error_response(lock_message, status=403)

            if pre_user.is_deleted or pre_user.deleted_at:
                logger.warning(f'Login attempt on deleted account: {pre_user.id}')
                return error_response('Invalid credentials', status=401)

            if not pre_user.email_verified:
                logger.info(f'Login blocked — email not verified: {pre_user.id}')
                return error_response(
                    'Please verify your email address before logging in.',
                    status=403
                )
            # ── End pre-validation ─────────────────────────────────

            dto_data = LoginRequestDTO(**data)
            success, user_dict = _interface.login_user(dto_data)
            
            if not success:
                record_login_attempt(pre_user, success=False, ip_address=get_user_ip())
                return error_response('Invalid credentials', status=401)
            
            # Post-validation / Success
            record_login_attempt(pre_user, success=True, ip_address=get_user_ip())
            ActivityLog.log(
                action='user_login',
                user_id=pre_user.id,
                entity_type='User',
                entity_id=pre_user.id,
                description=f'User logged in from IP {get_user_ip()}',
                ip_address=get_user_ip(),
                user_agent=request.headers.get('User-Agent'),
            )
            
            logger.info(f'User {user_dict.get("email")} logged in successfully')
            return success_response(user_dict)

        except (NotFound, InvalidCredentials):
            if 'pre_user' in locals() and pre_user:
                record_login_attempt(pre_user, success=False, ip_address=get_user_ip())
            return error_response('Invalid credentials', status=401)
            
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

            if user_id:
                ActivityLog.log(
                    action='user_logout',
                    user_id=user_id,
                    entity_type='User',
                    entity_id=user_id,
                    description=f'User logged out from IP {ip}',
                    ip_address=ip,
                    user_agent=request.headers.get('User-Agent'),
                )
                logger.info(f'User {user_id} logged out successfully.')

            resp_tuple = success_response('Logged out successfully')
            resp = resp_tuple[0]
            
            resp.delete_cookie(
                current_app.config.get('SESSION_COOKIE_NAME', 'tuned_session'),
                path=current_app.config.get('SESSION_COOKIE_PATH', '/'),
                domain=current_app.config.get('SESSION_COOKIE_DOMAIN'),
                samesite=current_app.config.get('SESSION_COOKIE_SAMESITE', 'None')
            )
            return resp_tuple

        except Exception as e:
            logger.error(f'Logout error: {str(e)}')
            return error_response('Logout failed', status=500)