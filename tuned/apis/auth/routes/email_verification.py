from __future__ import annotations

import logging

from flask import request
from flask.views import MethodView
from marshmallow import ValidationError

from tuned.apis.auth.schemas import EmailVerifyResendSchema, EmailVerifyConfirmSchema
from tuned.core.exceptions import NotFound
from tuned.core.logging import get_logger
from tuned.dtos import EmailVerificationResendDTO, EmailVerifyConfirmDTO
from tuned.interface import user as _interface
from tuned.utils.auth import get_user_ip, get_user_agent
from tuned.utils.decorators import rate_limit
from tuned.utils.responses import (
    error_response,
    success_response,
    validation_error_response,
)

logger: logging.Logger = get_logger(__name__)


class EmailVerificationResend(MethodView):
    decorators = [rate_limit(max_requests=3, window=900)]

    def post(self) -> tuple:
        try:
            schema = EmailVerifyResendSchema()
            data = schema.load(request.get_json(silent=True) or {})
        except ValidationError as err:
            logger.warning(f'[resend] Validation error: {err.messages}')
            return validation_error_response(err.messages)

        try:
            dto = EmailVerificationResendDTO(
                email=data['email'],
                ip_address=get_user_ip(),
                user_agent=get_user_agent(),
            )
            _interface.resend_verification_email(dto)
            return success_response({'message': 'If that address is registered, a new verification email has been sent.'})

        except ValueError as exc:
            raw = str(exc)
            if raw.startswith('rate_limited:'):
                seconds = raw.split(':')[1]
                return error_response(
                    f'Please wait {seconds} seconds before requesting another email.',
                    status=429,
                )
            logger.error(f'[resend] Unexpected ValueError: {exc!r}')
            return error_response('Could not send verification email. Please try again.', status=500)

        except Exception as exc:
            logger.error(f'[resend] Unhandled error: {exc!r}')
            return error_response('Could not send verification email. Please try again.', status=500)


class EmailVerifyConfirm(MethodView):
    def get(self) -> tuple:
        try:
            schema = EmailVerifyConfirmSchema()
            data = schema.load(request.args.to_dict())
        except ValidationError as err:
            logger.warning(f'[confirm] Validation error: {err.messages}')
            return validation_error_response(err.messages)

        try:
            dto = EmailVerifyConfirmDTO(
                uid=data['uid'],
                token=data['token'],
                ip_address=get_user_ip(),
                user_agent=get_user_agent(),
            )
            success, reason = _interface.confirm_email_verification(dto)

            if success:
                logger.info(f'[confirm] Email verified for uid={dto.uid}')
                return success_response({'verified': True})

            if reason == 'already_verified':
                logger.info(f'[confirm] Already verified uid={dto.uid}')
                return success_response({'verified': True, 'already_verified': True})

            status_map: dict[str, tuple[int, str]] = {
                'expired': (
                    410,
                    'This verification link has expired. Please request a new one.',
                ),
                'invalid': (
                    400,
                    'This verification link is invalid. Please request a new one.',
                ),
                'not_found': (
                    404,
                    'User account not found. Please register again.',
                ),
                'no_token': (
                    400,
                    'No verification token found. Please request a new verification email.',
                ),
            }
            http_status, message = status_map.get(
                reason, (400, 'Verification failed. Please request a new link.')
            )
            logger.warning(f'[confirm] Verification failed uid={dto.uid} reason={reason}')
            return error_response(message, status=http_status)

        except Exception as exc:
            logger.error(f'[confirm] Unhandled error uid={data.get("uid")}: {exc!r}')
            return error_response('Verification failed. Please try again.', status=500)
