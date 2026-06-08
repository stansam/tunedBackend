from flask import request
from flask_login import current_user
from flask.views import MethodView
from tuned.utils.dependencies import get_services
from tuned.utils.responses import (
    success_response,
    error_response,
    validation_error_response,
    created_response
)
from tuned.utils.decorators import rate_limit
from tuned.dtos.communication import NewsletterSubscribeDTO
from tuned.apis.main.schemas import NewsletterSubscribeSchema
from tuned.core.logging import get_logger
from marshmallow import ValidationError
import logging
from typing import Any

logger: logging.Logger = get_logger(__name__)


class NewsletterSubscribeView(MethodView):
    decorators = [rate_limit(max_requests=3, window=3600)]

    def post(self) -> tuple[Any, int]:
        try:
            schema = NewsletterSubscribeSchema()
            data = schema.load(request.get_json() or {})
        except ValidationError as err:
            return validation_error_response(err.messages)
        
        try:
            if current_user and current_user.is_authenticated:
                subscribe_dto = NewsletterSubscribeDTO(
                    email=current_user.email,
                    name=current_user.get_name(),
                    client_id=current_user.id
                )
            else:
                subscribe_dto = NewsletterSubscribeDTO(
                    email=data['email'],
                    name=data.get('name')
                )
            
            _ = get_services().newsletter.subscribe(
                data=subscribe_dto,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            # TODO: Check if it was a re-subscription or new
            
            return success_response(
                {'subscribed': True},
                message='Successfully processed newsletter subscription'
            )
            
        except Exception as e:
            logger.error(f'Error processing newsletter subscription: {str(e)}')
            return error_response('Failed to process subscription', status=500)
