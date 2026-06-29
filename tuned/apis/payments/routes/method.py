from dataclasses import asdict
import logging
from flask.views import MethodView
from flask_login import login_required
from tuned.utils import success_response
from tuned.utils.responses import error_response
from tuned.utils.dependencies import get_services

logger = logging.getLogger(__name__)

class PaymentMethodsView(MethodView):
    decorators = [login_required]

    def get(self):
        try:
            methods = get_services()._repos.payment.accepted_method.get_all_active()
            return success_response(
                data=[asdict(m) for m in methods], message="Payment methods fetched successfully", status=200
            )
        except Exception as e:
            logger.error(f"Failed to fetch payment methods: {e}")
            return error_response(message="Failed to fetch payment methods", status=500)
