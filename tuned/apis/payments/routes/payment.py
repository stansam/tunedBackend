from dataclasses import asdict
import logging
from flask import request, current_app, send_file
from flask.views import MethodView
from flask_login import login_required, current_user
from marshmallow import ValidationError
from datetime import datetime, timezone

from tuned.utils import success_response
from tuned.utils.responses import error_response
from tuned.utils.dependencies import get_services
from tuned.utils.decorators import rate_limit, admin_required
from tuned.models import MethodCategory, PaymentStatus, OrderStatus
from tuned.dtos.payment import PaymentResponseDTO
from tuned.apis.payments.schemas import CheckoutSchema, AdminRejectSchema

logger = logging.getLogger(__name__)

class CheckoutView(MethodView):
    decorators = [login_required, rate_limit(max_requests=5, window=60, key_prefix="checkout")]

    def post(self):
        services = None
        try:
            services = get_services()
            data = request.get_json()
            if not data:
                return error_response(message="No input data provided", status=400)

            try:
                validated = CheckoutSchema().load(data)
            except ValidationError as err:
                return error_response(message="Validation failed", status=400)

            order_id = validated["order_id"]
            method_id = validated["payment_method_id"]
            proof_ref = validated.get("client_proof_reference")

            order = services._repos.order.get_by_id(order_id)
            if not order:
                return error_response(message="Order not found", status=404)
            if str(order.client_id) != str(current_user.id):
                return error_response(message="Forbidden: Order does not belong to you", status=403)
            if order.paid:
                return error_response(message="Order has already been paid", status=400)
            if order.status == OrderStatus.CANCELED:
                return error_response(message="Order has been canceled", status=400)

            method = services._repos.payment.accepted_method.get_by_id(method_id)
            if not method:
                return error_response(message="Payment method not found or inactive", status=404)

            if method.category == MethodCategory.CREDIT_CARD:
                try:
                    result = services.payment.payment.initiate_pesapal_checkout(
                        order_id=str(order.id),
                        user_id=str(current_user.id),
                        amount=float(str(order.total_price)),
                        method_id=str(method.id),
                        user_data={
                            "email": current_user.email,
                            "phone": getattr(current_user, 'phone_number', '') or '',
                            "first_name": getattr(current_user, 'first_name', '') or '',
                            "last_name": getattr(current_user, 'last_name', '') or '',
                            "order_number": order.order_number,
                        },
                    )
                    return success_response(
                        data={
                            "action": "redirect",
                            "redirect_url": result["redirect_url"],
                            "order_tracking_id": result["order_tracking_id"],
                            "payment_id": result["payment_id"],
                            "payment_ref": result["payment_ref"],
                        },
                        message="Checkout initialized. Redirecting to secure payment page.",
                        status=200,
                    )
                except Exception as ex:
                    logger.error("[CheckoutView] Pesapal initiation failed: %r", ex)
                    if services is not None:
                        services._repos.session.rollback()
                    return error_response(message="Failed to initiate payment gateway. Please try again.", status=502)

            else:
                # Manual payment flow
                if proof_ref:
                    from tuned.core.exceptions import NotFound
                    try:
                        payment = services._repos.payment.payment.get_pending_payment_by_order_id(str(order.id), method.id)
                    except NotFound:
                        payment = None
                    
                    if not payment:
                        from tuned.dtos.payment import PaymentCreateDTO
                        payment_dto = PaymentCreateDTO(
                            order_id=str(order.id),
                            user_id=str(current_user.id),
                            amount=float(str(order.total_price)),
                            accepted_method_id=method.id,
                            status=PaymentStatus.PENDING
                        )
                        payment = services.payment.payment.process(payment_dto)

                    updated = services.payment.payment.mark_as_paid_client(str(payment.id), proof_ref, str(current_user.id))
                    return success_response(data={
                        "action": "manual",
                        "status": "pending_verification",
                        "payment_id": updated.id
                    }, message="Payment proof submitted successfully for verification", status=200)
                else:
                    return success_response(data={
                        "action": "manual",
                        "status": "pending_details",
                        "details": method.details,
                        "payment_method_name": method.name
                    }, message="Please transfer the amount to the details provided and submit proof reference.", status=200)

        except Exception as e:
            logger.error(f"Checkout error: {e}")
            if services is not None:
                services._repos.session.rollback()
            return error_response(message="Failed to process checkout", status=500)

class AdminVerifyPaymentView(MethodView):
    decorators = [login_required, admin_required]

    def put(self, payment_id):
        services = get_services()
        try:
            updated_payment = services.payment.payment.verify_payment(payment_id, str(current_user.id))
            return success_response(
                data={"payment_id": updated_payment.id, "status": "completed"},
                message="Payment manual proof successfully verified and order activated",
                status=200
            )
        except ValueError as val_ex:
            logger.error(f"Failed to verify payment {payment_id}: {val_ex}")
            return error_response(message=str(val_ex), status=400)
        except Exception as e:
            logger.error(f"Failed to verify payment {payment_id}: {e}")
            services._repos.session.rollback()
            return error_response(message="Failed to verify payment manual proof", status=500)

class AdminRejectPaymentView(MethodView):
    decorators = [login_required, admin_required]

    def put(self, payment_id):
        services = get_services()
        try:
            data = request.get_json()
            if not data:
                return error_response(message="No input data provided", status=400)

            try:
                validated = AdminRejectSchema().load(data)
            except ValidationError as err:
                return error_response(message="Validation failed", status=400)

            rejection_reason = validated["rejection_reason"]
            from tuned.utils.auth import get_user_ip, get_user_agent
            updated_payment = services.payment.payment.mark_as_failed(
                payment_id, current_user.id, rejection_reason, get_user_ip(), get_user_agent()
            )
            return success_response(
                data={"payment_id": updated_payment.id, "status": "failed"},
                message="Payment manual proof successfully rejected",
                status=200
            )
        except Exception as e:
            logger.error(f"Failed to reject payment {payment_id}: {e}")
            services._repos.session.rollback()
            return error_response(message="Failed to reject payment manual proof", status=500)

class ListPaymentsView(MethodView):
    decorators = [login_required]

    def get(self):
        try:
            services = get_services()
            status = request.args.get("status")
            page = request.args.get("page", 1, type=int)
            per_page = request.args.get("per_page", 10, type=int)

            user_id = None
            if not current_user.is_admin:
                user_id = str(current_user.id)
            else:
                filter_user_id = request.args.get("user_id")
                if filter_user_id:
                    user_id = filter_user_id

            payments, total = services.payment.payment.list_payments(
                user_id=user_id, status=status, page=page, per_page=per_page
            )
            from tuned.utils.responses import paginated_response
            return paginated_response(
                items=[asdict(p) for p in payments], page=page, per_page=per_page, total=total,
                message="Payments fetched successfully"
            )
        except Exception as e:
            logger.error(f"Failed to list payments: {e}")
            return error_response(message="Failed to fetch payments list", status=500)

class GetOrderPaymentView(MethodView):
    decorators = [login_required]

    def get(self, order_id: str):
        try:
            services = get_services()
            order = services._repos.order.get_by_id(order_id)
            if not order:
                return error_response(message="Order not found", status=404)
            if not current_user.is_admin and str(order.client_id) != str(current_user.id):
                return error_response(message="Forbidden: Order does not belong to you", status=403)

            payment = services._repos.payment.payment.get_active_payment_for_order(order_id)
            if not payment:
                return error_response(message="No active payment found for this order", status=404)

            return success_response(
                data=PaymentResponseDTO.from_model(payment).__dict__,
                message="Payment fetched successfully",
                status=200,
            )
        except Exception as e:
            logger.error("[GetOrderPaymentView] Error: %r", e)
            return error_response(message="Failed to fetch payment for order", status=500)

class DownloadInvoiceView(MethodView):
    decorators = [login_required]

    def get(self, payment_id):
        try:
            services = get_services()
            payment = services._repos.payment.payment.get_by_id(payment_id)
            if not payment:
                return error_response(message="Payment not found", status=404)
            if not current_user.is_admin and str(payment.user_id) != str(current_user.id):
                return error_response(message="Forbidden: Access denied", status=403)

            order = services._repos.order.get_by_id(str(payment.order_id))
            if not order:
                return error_response(message="Order not found", status=404)

            invoice_record = services._repos.payment.invoice.get_by_payment_id(payment_id)
            from tuned.services.pdf_service import generate_invoice_pdf
            pdf_buffer = generate_invoice_pdf(order=order, invoice=invoice_record)
            filename = f"Invoice_{invoice_record.invoice_number if invoice_record else order.order_number}.pdf"

            return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")
        except Exception as e:
            logger.error(f"Failed to download invoice: {e}")
            return error_response(message="Failed to generate invoice download", status=500)

class DownloadReceiptView(MethodView):
    decorators = [login_required]

    def get(self, payment_id):
        try:
            services = get_services()
            payment = services._repos.payment.payment.get_by_id(payment_id)
            if not payment:
                return error_response(message="Payment not found", status=404)
            if not current_user.is_admin and str(payment.user_id) != str(current_user.id):
                return error_response(message="Forbidden: Access denied", status=403)
            if payment.status != PaymentStatus.COMPLETED and payment.status != PaymentStatus.COMPLETED.value:
                return error_response(message="Receipt is only available for completed payments", status=400)

            from tuned.services.pdf_service import generate_receipt_pdf
            pdf_buffer = generate_receipt_pdf(payment=payment)
            filename = f"Receipt_{payment.payment_id}.pdf"

            return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")
        except Exception as e:
            logger.error(f"Failed to download receipt: {e}")
            return error_response(message="Failed to generate receipt download", status=500)
