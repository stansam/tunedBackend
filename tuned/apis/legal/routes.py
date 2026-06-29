from typing import Any
from flask import request
from flask_login import current_user, login_required
from flask.views import MethodView
from tuned.utils.dependencies import get_services
from tuned.utils.responses import success_response, error_response
from tuned.core.logging import get_logger

logger = get_logger(__name__)

class PoliciesAPI(MethodView):
    def get(self) -> tuple[Any, int]:
        try:
            legal_service = get_services().legal
            return success_response(legal_service.get_policies())
        except Exception as e:
            logger.error(f"Error fetching policy versions: {e}")
            return error_response("Failed to fetch policy versions", status=500)

class StatusAPI(MethodView):
    def get(self) -> tuple[Any, int]:
        try:
            if not current_user.is_authenticated:
                return success_response({"needsAcceptance": False})
            
            legal_service = get_services().legal
            needs_acceptance = legal_service.check_status(str(current_user.id))
            return success_response({"needsAcceptance": needs_acceptance})
        except Exception as e:
            logger.error(f"Error checking policy status: {e}")
            return error_response("Failed to check policy status", status=500)

class AcceptAPI(MethodView):
    decorators = [login_required]

    def post(self) -> tuple[Any, int]:
        try:
            body = request.get_json() or {}
            terms = body.get("terms")
            privacy = body.get("privacy")
            
            if not terms or not privacy:
                return error_response("Missing required policy versions ('terms', 'privacy')", status=400)
                
            ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)
            if ip_address and "," in ip_address:
                ip_address = ip_address.split(",")[0].strip()
            user_agent = request.user_agent.string
            
            legal_service = get_services().legal
            legal_service.accept_policies(
                user_id=str(current_user.id),
                terms_version=terms,
                privacy_version=privacy,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return success_response(message="Consent recorded successfully.")
        except Exception as e:
            logger.error(f"Error accepting policies: {e}")
            return error_response("Failed to record policy acceptance", status=500)
