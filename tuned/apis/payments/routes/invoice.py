from dataclasses import asdict
import logging
from flask import request
from flask.views import MethodView
from flask_login import login_required, current_user
from tuned.utils import success_response
from tuned.utils.responses import error_response
from tuned.utils.dependencies import get_services

logger = logging.getLogger(__name__)

class ListInvoicesView(MethodView):
    decorators = [login_required]

    def get(self):
        try:
            services = get_services()
            page = request.args.get("page", 1, type=int)
            per_page = request.args.get("per_page", 10, type=int)

            if current_user.is_admin:
                user_id = request.args.get("user_id") or str(current_user.id)
            else:
                user_id = str(current_user.id)

            invoices, total = services._repos.payment.invoice.list_by_user(
                user_id=user_id, page=page, per_page=per_page
            )
            from tuned.utils.responses import paginated_response
            return paginated_response(
                items=[asdict(i) for i in invoices], page=page, per_page=per_page, total=total,
                message="Invoices fetched successfully",
            )
        except Exception as e:
            logger.error("[ListInvoicesView] Error: %r", e)
            return error_response(message="Failed to fetch invoices", status=500)

class GetInvoiceView(MethodView):
    decorators = [login_required]

    def get(self, invoice_id: str):
        try:
            services = get_services()
            invoice = services._repos.payment.invoice.get_by_id(invoice_id)
            if not invoice:
                return error_response(message="Invoice not found", status=404)
            if not current_user.is_admin and str(invoice.user_id) != str(current_user.id):
                return error_response(message="Forbidden: Access denied", status=403)

            return success_response(data=asdict(invoice), message="Invoice fetched successfully", status=200)
        except Exception as e:
            logger.error("[GetInvoiceView] Error: %r", e)
            return error_response(message="Failed to fetch invoice", status=500)
