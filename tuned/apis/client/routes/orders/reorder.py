import logging
from tuned.interface import order as _order_service
from tuned.core.logging import get_logger
from tuned.utils.responses import success_response, error_response
from flask_login import login_required, current_user
from flask.views import MethodView
from dataclasses import asdict
from typing import Any

logger: logging.Logger = get_logger(__name__)

class ReorderOrder(MethodView):
    decorators = [login_required]

    def post(self, order_id: str) -> tuple[Any, int]:
        try:
            dto = _order_service.reorder(order_id, str(current_user.id))
            return success_response(data=asdict(dto), message="Successfully created", status=201)
        except Exception as e:
            logger.error("Failed to create reorder: %s", e)
            return error_response(message="Failed to create reorder", status=500)
