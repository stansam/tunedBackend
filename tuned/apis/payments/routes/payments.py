from dataclasses import asdict
import logging
from flask import request, current_app, send_file
from flask.views import MethodView
from flask_login import login_required, current_user
from marshmallow import ValidationError
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from uuid import UUID

from tuned.utils import success_response
from tuned.utils.responses import error_response
from tuned.utils.dependencies import get_services
from tuned.utils.auth import get_user_ip, get_user_agent
from tuned.utils.decorators import rate_limit, admin_required
from tuned.models import (
    AcceptedPaymentMethod, Payment, PaymentStatus, Order, OrderStatus, 
    MethodCategory, NotificationType, User
)
from tuned.dtos.payment import (
    PaymentCreateDTO, PaymentUpdateDTO, InvoiceCreateDTO, PaymentResponseDTO
)
from tuned.dtos.notification import NotificationCreateDTO
from tuned.apis.payments.schemas import CheckoutSchema, AdminRejectSchema
from tuned.interface.payment.pesapal import PesapalHelper
from tuned.utils.email import send_async_email
from tuned.extensions import socketio

logger = logging.getLogger(__name__)

class PaymentMethodsView(MethodView):
    decorators = [login_required]

    def get(self):
        try:
            methods = get_services()._repos.payment.accepted_method.get_all_active()
            return success_response(
                data=[asdict(m) for m in methods],
                message="Payment methods fetched successfully",
                status=200
            )
        except Exception as e:
            logger.error(f"Failed to fetch payment methods: {e}")
            return error_response(message="Failed to fetch payment methods", status=500)


class CheckoutView(MethodView):
    decorators = [login_required]

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
                logger.error(f"Validation failed: {err.messages}", exc_info=True)
                return error_response(message="Validation failed", status=400)

            order_id = validated["order_id"]
            method_id = validated["payment_method_id"]
            proof_ref = validated.get("client_proof_reference")

            # 1. Fetch Order and verify ownership
            order = services._repos.order.get_by_id(order_id)
            if not order:
                logger.error(f"Order not found: {order_id}")
                return error_response(message="Order not found", status=404)
            if str(order.client_id) != str(current_user.id):
                logger.error(f"Order does not belong to user: {order_id}")
                return error_response(message="Forbidden: Order does not belong to you", status=403)
            if order.paid:
                logger.error(f"Order has already been paid: {order_id}")
                return error_response(message="Order has already been paid", status=400)
            if order.status == OrderStatus.CANCELED:
                return error_response(message="Order has been canceled", status=400)

            # 2. Fetch Payment Method
            method = services._repos.payment.accepted_method.get_by_id(method_id)
            if not method:
                logger.error(f"Payment method not found or inactive: {method_id}")
                return error_response(message="Payment method not found or inactive", status=404)

            # 3. Separate Flows: Automated (Pesapal Card) vs Manual (Bank, Digital Wallet, etc.)
            if method.category == MethodCategory.CREDIT_CARD:
                # Automated Checkout via Pesapal V3 gateway
                try:
                    pesapal = PesapalHelper()
                    
                    # Create the pending payment record in our DB first
                    payment_dto = PaymentCreateDTO(
                        order_id=str(order.id),
                        user_id=str(current_user.id),
                        amount=float(str(order.total_price)),
                        accepted_method_id=method.id,
                        status=PaymentStatus.PENDING
                    )
                    payment_resp = services.payment.payment.process(payment_dto)
                    
                    # Submit transaction to Pesapal V3
                    sub_res = pesapal.submit_order(
                        order_id=str(order.id),
                        amount=float(str(order.total_price)),
                        email=current_user.email,
                        phone=current_user.phone_number,
                        first_name=current_user.first_name,
                        last_name=current_user.last_name,
                        description=f"Fulfillment Payment for Order #{order.order_number}"
                    )
                    
                    redirect_url = sub_res.get("redirect_url")
                    order_tracking_id = sub_res.get("order_tracking_id")
                    
                    if not redirect_url or not order_tracking_id:
                        raise ValueError(f"Invalid Pesapal response: {sub_res}")
                    
                    # Store tracking ID in our client_proof_reference for automated IPN verification
                    payment_resp = services.payment.payment.mark_as_paid_client(payment_resp.id, order_tracking_id, current_user.id)
                    services._repos.payment.save()

                    return success_response(data={
                        "action": "redirect",
                        "redirect_url": redirect_url,
                        "payment_id": payment_resp.id
                    }, message="Checkout redirect initialized", status=200)
                    
                except Exception as ex:
                    logger.error(f"Pesapal checkout failed: {ex}")
                    services._repos.session.rollback()
                    return error_response(message=f"Gateway payment failed: {str(ex)}", status=502)

            else:
                # Manual payment flow
                if proof_ref:
                    payment = services._repos.payment.payment.get_pending_payment_by_order_id(str(order.id), method.id)
                    
                    if not payment:
                        payment_dto = PaymentCreateDTO(
                            order_id=str(order.id),
                            user_id=str(current_user.id),
                            amount=float(str(order.total_price)),
                            accepted_method_id=method.id,
                            status=PaymentStatus.PENDING
                        )
                        payment = services.payment.payment.process(payment_dto)

                    # Mark payment as paid and transition state
                    updated = services.payment.payment.mark_as_paid_client(str(payment.id), proof_ref, str(current_user.id))

                    return success_response(data={
                        "action": "manual",
                        "status": "pending_verification",
                        "payment_id": updated.id
                    }, message="Payment proof submitted successfully for verification", status=200)

                else:
                    # Requesting bank/wallet details to pay
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


class PesapalIpnView(MethodView):
    decorators = [rate_limit(max_requests=30, window=60, key_prefix="pesapal_ipn")]

    def get(self):
        """
        Pesapal Instant Payment Notification (IPN) webhook listener.
        Secured by direct verification checks against official Pesapal transaction status.
        """
        # Verify caller IP in non-development environments
        if current_app.config.get("FLASK_ENV") == "production":
            from tuned.interface.payment.pesapal import PESAPAL_IPN_ALLOWED_IPS
            caller_ip = get_user_ip()
            if caller_ip not in PESAPAL_IPN_ALLOWED_IPS:
                logger.warning(f"[IPN] Rejected request from unauthorized IP: {caller_ip}")
                return error_response(message="Forbidden", status=403)

        services = None
        try:
            services = get_services()
            order_tracking_id = request.args.get("OrderTrackingId")
            order_merchant_ref = request.args.get("OrderMerchantReference")
            notif_type = request.args.get("OrderNotificationType")

            if not order_tracking_id:
                logger.error("[IPN] Missing tracking parameter")
                return error_response(message="Missing tracking parameter", status=400)

            logger.info(f"[IPN] Received Pesapal IPN update: TrackingId={order_tracking_id}, Ref={order_merchant_ref}, Type={notif_type}")

            # 1. Query Transaction Status directly from Pesapal for maximum security (Payload verification)
            pesapal = PesapalHelper()
            status_res = pesapal.get_transaction_status(order_tracking_id)
            
            status_description = status_res.get("payment_status_description", "").lower()
            amount_paid = status_res.get("amount", 0.0)
            logger.info(f"[IPN] Verified status from Pesapal API: {status_description} (Amount: {amount_paid})")

            if status_description == "completed" or status_description == "success":
                # Get the pending payment bound to this tracking ID
                payment = services._repos.payment.payment.get_pending_payment_by_reference_id(order_tracking_id)
                
                if payment:
                    
                    _ = services.payment.payment.verify_payment(str(payment.id), "system")
                    logger.info(f"[IPN] Payment {payment.id} verified via IPN for Order {payment.order_id}")
                else:
                    logger.warning(f"[IPN] Completed transaction has already been verified or no pending record exists: {order_tracking_id}")
            
            # Pesapal expects a JSON acknowledgment returned
            return {"response": "OK", "status": 200}

        except Exception as e:
            logger.error(f"[IPN] Failed to verify webhook update: {e}")
            if services is not None:
                services._repos.session.rollback()
            return error_response(message="Failed to handle webhook status check", status=500)


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
                logger.error(f"Failed to reject payment {payment_id}: No input data provided")
                return error_response(message="No input data provided", status=400)

            try:
                validated = AdminRejectSchema().load(data)
            except ValidationError as err:
                logger.error(f"Failed to reject payment {payment_id}: {err}")
                return error_response(message="Validation failed", status=400)

            rejection_reason = validated["rejection_reason"]
            updated_payment = services.payment.payment.mark_as_failed(payment_id, current_user.id, rejection_reason, get_user_ip(), get_user_agent())

            logger.info(f"Payment proof {payment_id} rejected by admin {current_user.id}")
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
                # If admin, let them optionally filter by user_id
                filter_user_id = request.args.get("user_id")
                if filter_user_id:
                    user_id = filter_user_id

            payments, total = services.payment.payment.list_payments(
                user_id=user_id,
                status=status,
                page=page,
                per_page=per_page
            )

            from tuned.utils.responses import paginated_response
            return paginated_response(
                items=[asdict(p) for p in payments],
                page=page,
                per_page=per_page,
                total=total,
                message="Payments fetched successfully"
            )
        except Exception as e:
            logger.error(f"Failed to list payments: {e}")
            return error_response(message="Failed to fetch payments list", status=500)


class DownloadInvoiceView(MethodView):
    decorators = [login_required]

    def get(self, payment_id):
        try:
            services = get_services()
            payment = services._repos.payment.payment.get_by_id(payment_id)
            if not payment:
                return error_response(message="Payment not found", status=404)

            # Security: Must be owner or admin
            if not current_user.is_admin and str(payment.user_id) != str(current_user.id):
                return error_response(message="Forbidden: Access denied", status=403)

            order = services._repos.order.get_by_id(str(payment.order_id))
            if not order:
                return error_response(message="Order not found", status=404)

            invoice_record = services._repos.payment.invoice.get_by_payment_id(payment_id)

            # Generate PDF Invoice using reports lab utility
            from tuned.services.pdf_service import generate_invoice_pdf
            
            pdf_buffer = generate_invoice_pdf(order=order, invoice=invoice_record)
            filename = f"Invoice_{invoice_record.invoice_number if invoice_record else order.order_number}.pdf"

            return send_file(
                pdf_buffer,
                as_attachment=True,
                download_name=filename,
                mimetype="application/pdf"
            )
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

            # Security: Must be owner or admin
            if not current_user.is_admin and str(payment.user_id) != str(current_user.id):
                return error_response(message="Forbidden: Access denied", status=403)

            if payment.status != PaymentStatus.COMPLETED and payment.status != PaymentStatus.COMPLETED.value:
                return error_response(message="Receipt is only available for completed payments", status=400)

            # Generate PDF Receipt
            from tuned.services.pdf_service import generate_receipt_pdf
            
            pdf_buffer = generate_receipt_pdf(payment=payment)
            filename = f"Receipt_{payment.payment_id}.pdf"

            return send_file(
                pdf_buffer,
                as_attachment=True,
                download_name=filename,
                mimetype="application/pdf"
            )
        except Exception as e:
            logger.error(f"Failed to download receipt: {e}")
            return error_response(message="Failed to generate receipt download", status=500)

