import logging
from flask import request
from flask.views import MethodView
from flask_login import login_required
from marshmallow import ValidationError
from dataclasses import asdict

from tuned.utils import success_response
from tuned.utils.responses import error_response
from tuned.utils.decorators import rate_limit
from tuned.apis.payments.schemas import ValidateCheckoutDiscountSchema

logger = logging.getLogger(__name__)

class ValidateDiscountAtCheckoutView(MethodView):
    decorators = [login_required, rate_limit(max_requests=10, window=60, key_prefix="discount_checkout")]

    def post(self):
        try:
            data = request.get_json()
            if not data:
                return error_response(message="No input data provided", status=400)

            try:
                validated = ValidateCheckoutDiscountSchema().load(data)
            except ValidationError:
                return error_response(message="Validation failed", status=400)

            code = validated["code"]
            order_total = validated["order_total"]

            from tuned.utils.dependencies import get_services
            resp = get_services().order.validate_discount(code, order_total)
            return success_response(data=asdict(resp), message="Discount validated", status=200)
        except Exception as e:
            logger.error("[ValidateDiscountAtCheckoutView] Error: %r", e)
            return error_response(message="Failed to validate discount", status=500)
