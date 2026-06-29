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
from tuned.utils.auth import get_user_ip, get_user_agent
from marshmallow import ValidationError
import logging
from typing import Any

logger: logging.Logger = get_logger(__name__)


class NewsletterSubscribeView(MethodView):
    decorators = [rate_limit(max_requests=10, window=3600)]

    def post(self) -> tuple[Any, int]:
        try:
            schema = NewsletterSubscribeSchema()
            data = schema.load(request.get_json() or {})
        except ValidationError as err:
            return validation_error_response(err.messages)
        
        try:
            email_val = data['email']
            name_val = data.get('name')
            client_id_val = None

            if current_user and current_user.is_authenticated:
                if current_user.email.strip().lower() == email_val.strip().lower():
                    name_val = current_user.get_name()
                    client_id_val = current_user.id

            subscribe_dto = NewsletterSubscribeDTO(
                email=email_val,
                name=name_val,
                client_id=client_id_val
            )
            
            _ = get_services().newsletter.subscribe(
                data=subscribe_dto,
                ip_address=get_user_ip(),
                user_agent=get_user_agent()
            )
            
            # TODO: Check if it was a re-subscription or new
            
            return success_response(
                {'subscribed': True},
                message='Successfully processed newsletter subscription'
            )
            
        except Exception as e:
            logger.error(f'Error processing newsletter subscription: {str(e)}')
            return error_response('Failed to process subscription', status=500)
