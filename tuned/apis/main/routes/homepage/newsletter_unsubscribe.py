from flask import request, current_app
from flask.views import MethodView
from itsdangerous import URLSafeSerializer, BadSignature, SignatureExpired
from tuned.utils.dependencies import get_services
from tuned.utils.responses import success_response, error_response
from tuned.core.logging import get_logger
from tuned.utils.auth import get_user_ip, get_user_agent
import logging
from typing import Any

logger: logging.Logger = get_logger(__name__)


class NewsletterUnsubscribeView(MethodView):
    def get(self) -> tuple[Any, int]:
        try:
            token = request.args.get("token")
            if not token:
                return error_response("Token is required", status=400)

            secret_key = current_app.config.get("SECRET_KEY", "default-secret-key")
            serializer = URLSafeSerializer(secret_key, salt="newsletter-unsubscribe")
            
            try:
                email = serializer.loads(token)
            except (BadSignature, SignatureExpired) as sig_err:
                logger.warning(f"Failed to verify unsubscribe token: {str(sig_err)}")
                return error_response("Invalid or expired token", status=400)

            return success_response(
                {"email": email},
                message="Token is valid"
            )
        except Exception as e:
            logger.error(f"Error validating unsubscribe token: {str(e)}")
            return error_response("Failed to validate token", status=500)

    def post(self) -> tuple[Any, int]:
        try:
            data = request.get_json() or {}
            token = data.get("token")
            if not token:
                return error_response("Token is required", status=400)

            secret_key = current_app.config.get("SECRET_KEY", "default-secret-key")
            serializer = URLSafeSerializer(secret_key, salt="newsletter-unsubscribe")
            
            try:
                email = serializer.loads(token)
            except (BadSignature, SignatureExpired) as sig_err:
                logger.warning(f"Failed to verify unsubscribe token: {str(sig_err)}")
                return error_response("Invalid or expired token", status=400)

            get_services().newsletter.unsubscribe(
                email=email,
                ip_address=get_user_ip(),
                user_agent=get_user_agent()
            )

            return success_response(
                {"unsubscribed": True},
                message="Successfully unsubscribed from newsletter"
            )

        except Exception as e:
            logger.error(f"Error processing newsletter unsubscription: {str(e)}")
            return error_response("Failed to process unsubscription", status=500)
