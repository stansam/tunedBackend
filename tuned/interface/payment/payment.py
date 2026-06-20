from __future__ import annotations
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, TYPE_CHECKING
from tuned.core.logging import get_logger
from tuned.dtos import (
    ActivityLogCreateDTO, PaymentCreateDTO, PaymentUpdateDTO, PaymentResponseDTO,
    InvoiceCreateDTO, TransactionCreateDTO
)
from tuned.dtos.payment import (
    PesapalSubmitOrderDTO, PesapalSubmitOrderResponseDTO,
    PesapalTransactionStatusDTO, PaymentStatusResponseDTO,
)
from tuned.utils.variables import Variables
from tuned.core.events import get_event_bus
from tuned.models import PaymentStatus, OrderStatus, TransactionType, TransactionStatus

if TYPE_CHECKING:
    from tuned.repository import Repository

logger: logging.Logger = get_logger(__name__)
event_bus = get_event_bus()

class ProcessPayment:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.payment.payment
        self._repos = repos
        from tuned.interface.audit import AuditService
        self._audit = AuditService(repos=repos)

    def execute(self, data: PaymentCreateDTO) -> PaymentResponseDTO:
        try:
            payment = self._repo.create(data)
            
            try:
                self._repos.payment.transaction.create(TransactionCreateDTO(
                    payment_id=payment.id,
                    type=TransactionType.PAYMENT,
                    amount=payment.amount,
                    status=TransactionStatus.PENDING
                ))
            except Exception as tx_exc:
                logger.error(f"[ProcessPayment] Transaction record creation failed for payment {payment.id}: {tx_exc!r}")

            try:
                self._audit.activity_log.log(ActivityLogCreateDTO(
                    action=Variables.PAYMENT_CREATE_ACTION,
                    user_id=data.user_id,
                    entity_type=Variables.PAYMENT_ENTITY_TYPE,
                    entity_id=payment.id,
                    after=payment,
                    created_by=data.user_id,
                    ip_address="system",
                    user_agent="system"
                ))
            except Exception as audit_exc:
                logger.error(f"[ProcessPayment] Audit failed for payment {payment.id}: {audit_exc!r}")
            self._repos.payment.save()
            try:
                event_bus.emit("payment.created", {
                    "payment_id": payment.id,
                    "order_id": payment.order_id,
                    "user_id": payment.user_id,
                    "amount": payment.amount,
                    "status": payment.status.value if isinstance(payment.status, PaymentStatus) else str(payment.status)
                })
            except Exception as event_exc:
                logger.error(f"[ProcessPayment] Event emit failed for payment {payment.id}: {event_exc!r}")

            logger.info(f"[ProcessPayment] User {data.user_id} created payment {payment.id}")
            return payment
        except Exception as exc:
            logger.error(f"[ProcessPayment] Failed to process payment: {exc!r}")
            raise

class GetPaymentDetails:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.payment.payment

    def execute(self, payment_id: str) -> PaymentResponseDTO:
        try:
            payment = self._repo.get_by_id(payment_id)
            return PaymentResponseDTO.from_model(payment)
        except Exception as exc:
            logger.error(f"[GetPaymentDetails] Failed to get payment {payment_id}: {exc!r}")
            raise

class ClientMarkAsPaid:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.payment.payment
        self._repos = repos 
        from tuned.interface.audit import AuditService
        self._audit = AuditService(repos=repos)
        
    def execute(self, payment_id: str, client_proof_reference: str, client_id: str) -> PaymentResponseDTO:
        try:
            client = self._repos.user.get_user_by_id(client_id)
            payment = self._repo.get_by_id(payment_id)
            order = self._repos.order.get_by_id(str(payment.order_id))
            if payment.status != PaymentStatus.PENDING:
                raise ValueError(f"Payment is not in a pending state, current state: {payment.status}")
                
            data = PaymentUpdateDTO(
                status=PaymentStatus.PENDING_VERIFICATION,
                client_proof_reference=client_proof_reference,
                client_marked_paid_at=datetime.now(timezone.utc)
            )
            updated_payment = self._repo.update(payment_id, data)

            try:
                self._repos.payment.transaction.create(TransactionCreateDTO(
                    payment_id=str(updated_payment.id),
                    type=TransactionType.PAYMENT,
                    amount=updated_payment.amount,
                    status=TransactionStatus.PENDING,
                    reference=client_proof_reference
                ))
            except Exception as tx_exc:
                logger.error(f"[ClientMarkAsPaid] Transaction record creation failed for payment {updated_payment.id}: {tx_exc!r}")

            try:
                self._audit.activity_log.log(ActivityLogCreateDTO(
                    action=Variables.PAYMENT_UPDATE_ACTION,
                    user_id=str(updated_payment.user_id),
                    entity_type=Variables.PAYMENT_ENTITY_TYPE,
                    entity_id=str(updated_payment.id),
                    before=payment,
                    after=updated_payment,
                    created_by=client_id,
                    ip_address="system",
                    user_agent="system"
                ))
            except Exception as audit_exc:
                logger.error(f"[ClientMarkAsPaid] Audit failed for payment {updated_payment.id}: {audit_exc!r}")
            self._repos.payment.save()

            # Email confirmation to the client and admin
            try:
                from tuned.services.email_service import send_payment_client_marked_paid, send_admin_payment_proof_submitted
                send_payment_client_marked_paid(client, order, updated_payment)
                admin = self._repos.user.get_admin_user()
                send_admin_payment_proof_submitted(admin, updated_payment, client.get_name(), order.order_number)
            except Exception as email_exc:
                logger.error("[ClientMarkAsPaid] Email confirmation failed: %r", email_exc)

            try:
                method_category = None
                try:
                    method = self._repos.payment.accepted_method.get_by_id(str(updated_payment.accepted_method_id))
                    method_category = method.category.value if method else None
                except Exception:
                    pass

                event_bus.emit("payment.client_marked_paid", {
                    "payment_id":      str(updated_payment.id),
                    "order_id":        str(updated_payment.order_id),
                    "order_number":    order.order_number,
                    "user_id":         str(updated_payment.user_id),
                    "client_name":     client.get_name(),
                    "client_email":    client.email,
                    "status":          updated_payment.status.value if isinstance(updated_payment.status, PaymentStatus) else str(updated_payment.status),
                    "amount":          float(updated_payment.amount),
                    "method_category": method_category,
                })
            except Exception as event_exc:
                logger.error("[ClientMarkAsPaid] Event emit failed for payment %s: %r", updated_payment.id, event_exc)

            logger.info("[ClientMarkAsPaid] Payment %s marked as paid by client %s", updated_payment.id, client_id)
            return PaymentResponseDTO.from_model(updated_payment)
        except Exception as exc:
            logger.error("[ClientMarkAsPaid] Failed to mark payment %s as paid: %r", payment_id, exc)
            raise

class AdminVerifyPayment:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.payment.payment
        self._repos = repos
        from tuned.interface.audit import AuditService
        self._audit = AuditService(repos=repos)
        
    def execute(self, payment_id: str, admin_id: str, admin_notes: Optional[str] = None) -> PaymentResponseDTO:
        try:
            payment = self._repo.get_by_id(payment_id)
            if payment.status not in (PaymentStatus.PENDING, PaymentStatus.PENDING_VERIFICATION):
                raise ValueError(
                    f"Payment '{payment.payment_id}' cannot be verified in state: {payment.status.value}. "
                    f"Expected PENDING or PENDING_VERIFICATION."
                )
                
            data = PaymentUpdateDTO(
                status=PaymentStatus.COMPLETED,
                admin_verified_at=datetime.now(timezone.utc),
                admin_notes=admin_notes,
            )
            updated_payment = self._repo.update(payment_id, data)

            try:
                self._repos.payment.transaction.create(TransactionCreateDTO(
                    payment_id=str(updated_payment.id),
                    type=TransactionType.PAYMENT,
                    amount=updated_payment.amount,
                    status=TransactionStatus.COMPLETED,
                    reference=getattr(updated_payment, 'pesapal_tracking_id', None)
                ))
            except Exception as tx_exc:
                logger.error("[AdminVerifyPayment] Transaction record creation failed for payment %s: %r", updated_payment.id, tx_exc)

            order = self._repos.order.get_by_id(str(updated_payment.order_id))
            old_order_status = None
            invoice = None
            if order is not None:
                old_order_status = order.status
                order.paid = True
                order.status = OrderStatus.ACTIVE
                
                try:
                    due_date = order.due_date
                    if due_date is not None:
                        try:
                            due_date = due_date.isoformat()
                        except Exception as e: # TODO: Check this implementation later
                            logger.error("[AdminVerifyPayment] Failed to convert due_date to isoformat: %r", e)
                            due_date = None

                    event_bus.emit("order.status_changed", {
                        "order_id":    str(order.id),
                        "client_id":   str(order.client_id),
                        "order_number": order.order_number,
                        "old_status":  old_order_status.value if old_order_status else None,
                        "new_status":  OrderStatus.ACTIVE.value,
                        "title":       getattr(order, 'title', ''),
                        "due_date":    due_date,
                        "progress":    0,
                    })
                except Exception as order_event_exc:
                    logger.error("[AdminVerifyPayment] order.status_changed emit failed: %r", order_event_exc)

                # Auto-generate paid invoice
                invoice_dto = InvoiceCreateDTO(
                    order_id=str(order.id),
                    user_id=str(order.client_id),
                    subtotal=float(getattr(order, 'subtotal', None) or order.total_price or 0.0),
                    total=float(order.total_price or 0.0),
                    due_date=datetime.now(timezone.utc) + timedelta(days=14),
                    payment_id=str(updated_payment.id),
                    discount=float(getattr(order, 'discount_amount', None) or 0.0),
                    tax=0.0,
                    paid=True
                )
                invoice = self._repos.payment.invoice.create(invoice_dto)

            try:
                self._audit.activity_log.log(ActivityLogCreateDTO(
                    action=Variables.PAYMENT_UPDATE_ACTION,
                    user_id=str(updated_payment.user_id),
                    entity_type=Variables.PAYMENT_ENTITY_TYPE,
                    entity_id=str(updated_payment.id),
                    before=payment,
                    after=updated_payment,
                    created_by=admin_id,
                    ip_address="system",
                    user_agent="system"
                ))
            except Exception as audit_exc:
                logger.error("[AdminVerifyPayment] Audit failed for payment %s: %r", updated_payment.id, audit_exc)
            self._repos.payment.save()

            # Email notification
            client = None
            try:
                from tuned.services.email_service import send_client_payment_verification_success_email
                client = self._repos.user.get_user_by_id(str(updated_payment.user_id))
                send_client_payment_verification_success_email(user=client, payment=updated_payment, order=order)
            except Exception as email_exc:
                logger.error("[AdminVerifyPayment] Email confirmation failed: %r", email_exc)

            is_automated = admin_id.startswith("system")
            try:
                event_bus.emit("payment.verified_by_admin", {
                    "payment_id":    str(updated_payment.id),
                    "payment_ref":   updated_payment.payment_id,
                    "order_id":      str(updated_payment.order_id),
                    "order_number":  order.order_number if order is not None else "",
                    "user_id":       str(updated_payment.user_id),
                    "client_name":   client.get_name() if client is not None else "",
                    "client_email":  client.email if client is not None else "",
                    "status":        updated_payment.status.value if isinstance(updated_payment.status, PaymentStatus) else str(updated_payment.status),
                    "amount":        float(updated_payment.amount),
                    "is_automated":  is_automated,
                    "invoice_id":    str(invoice.id) if invoice else None,
                    "invoice_number": invoice.invoice_number if invoice else None,
                })
            except Exception as event_exc:
                logger.error("[AdminVerifyPayment] Event emit failed for payment %s: %r", updated_payment.id, event_exc)

            if invoice:
                try:
                    event_bus.emit("invoice.created", {
                        "invoice_id":     str(invoice.id),
                        "invoice_number": invoice.invoice_number,
                        "user_id":        str(updated_payment.user_id),
                        "order_id":       str(updated_payment.order_id),
                        "order_number":   order.order_number if order is not None else "",
                        "total":          float(invoice.total),
                        "payment_id":     str(updated_payment.id),
                    })
                except Exception as inv_event_exc:
                    logger.error("[AdminVerifyPayment] invoice.created emit failed: %r", inv_event_exc)

            logger.info("[AdminVerifyPayment] Payment %s verified by admin %s", updated_payment.id, admin_id)
            return PaymentResponseDTO.from_model(updated_payment)
        except Exception as exc:
            logger.error("[AdminVerifyPayment] Failed to verify payment %s: %r", payment_id, exc)
            raise

class AdminRejectPayment:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.payment.payment
        self._repos = repos
        from tuned.interface.audit import AuditService
        self._audit = AuditService(repos=repos)
        
    def execute(self, payment_id: str, user_id: str, rejection_reason: str = "Payment marked as failed by Admin", ip_address: str = "system", user_agent: str = "system") -> PaymentResponseDTO:
        try:
            payment = self._repo.get_by_id(payment_id)
            if payment.status not in (PaymentStatus.PENDING, PaymentStatus.PENDING_VERIFICATION):
                raise ValueError(f"Payment is not in correct status to reject, current state: {payment.status}")
                
            data = PaymentUpdateDTO(
                status=PaymentStatus.FAILED,
                admin_verified_at=datetime.now(timezone.utc),
                admin_notes=rejection_reason,
            )
            updated_payment = self._repo.update(payment_id, data)

            try:
                self._repos.payment.transaction.create(TransactionCreateDTO(
                    payment_id=str(updated_payment.id),
                    type=TransactionType.PAYMENT,
                    amount=updated_payment.amount,
                    status=TransactionStatus.FAILED,
                    reference=getattr(updated_payment, 'pesapal_tracking_id', None)
                ))
            except Exception as tx_exc:
                logger.error("[AdminRejectPayment] Transaction record creation failed for payment %s: %r", updated_payment.id, tx_exc)

            try:
                self._audit.activity_log.log(ActivityLogCreateDTO(
                    action=Variables.PAYMENT_UPDATE_ACTION,
                    user_id=str(updated_payment.user_id),
                    entity_type=Variables.PAYMENT_ENTITY_TYPE,
                    entity_id=str(updated_payment.id),
                    before=payment,
                    after=updated_payment,
                    created_by=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent
                ))
            except Exception as audit_exc:
                logger.error("[AdminRejectPayment] Audit failed for payment %s: %r", updated_payment.id, audit_exc)
            self._repos.payment.save()

            # Email notification
            try:
                from tuned.services.email_service import send_client_payment_verification_failure_email
                order = self._repos.order.get_by_id(str(updated_payment.order_id))
                client = self._repos.user.get_user_by_id(str(updated_payment.user_id))
                send_client_payment_verification_failure_email(client, order.order_number, rejection_reason)
            except Exception as email_exc:
                logger.error("[AdminRejectPayment] Email notification failed: %r", email_exc)

            try:
                order = self._repos.order.get_by_id(str(updated_payment.order_id))
                client = self._repos.user.get_user_by_id(str(updated_payment.user_id))
                event_bus.emit("payment.marked_failed", {
                    "payment_id":       str(updated_payment.id),
                    "order_id":         str(updated_payment.order_id),
                    "order_number":     order.order_number,
                    "user_id":          str(updated_payment.user_id),
                    "client_name":      client.get_name(),
                    "client_email":     client.email,
                    "status":           updated_payment.status.value if isinstance(updated_payment.status, PaymentStatus) else str(updated_payment.status),
                    "rejection_reason": rejection_reason,
                    "rejected_by":      user_id,
                })
            except Exception as event_exc:
                logger.error("[AdminRejectPayment] Event emit failed for payment %s: %r", updated_payment.id, event_exc)

            logger.info("[AdminRejectPayment] Payment %s rejected by admin %s", updated_payment.id, user_id)
            return PaymentResponseDTO.from_model(updated_payment)
        except Exception as exc:
            logger.error(f"[AdminRejectPayment] Failed to reject payment {payment_id}: {exc!r}")
            raise


class ListPayments:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.payment.payment

    def execute(self, user_id: Optional[str] = None, status: Optional[str] = None, page: int = 1, per_page: int = 10) -> tuple[list[PaymentResponseDTO], int]:
        try:
            return self._repo.list_payments(user_id=user_id, status=status, page=page, per_page=per_page)
        except Exception as exc:
            logger.error(f"[ListPayments] Failed to list payments: {exc!r}")
            raise


class InitiatePesapalCheckout:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.payment.payment
        self._repos = repos
        from tuned.interface.audit import AuditService
        self._audit = AuditService(repos=repos)

    def execute(
        self,
        order_id: str,
        user_id: str,
        amount: float,
        method_id: str,
        user_data: dict,
    ) -> dict:
        from tuned.interface.payment.pesapal import PesapalHelper

        # 1. Create the pending payment record first so we have a PAY-XXXX slug
        payment_dto = PaymentCreateDTO(
            order_id=order_id,
            user_id=user_id,
            amount=amount,
            accepted_method_id=method_id,
            status=PaymentStatus.PENDING,
        )
        payment = self._repo.create(payment_dto)
        logger.info(
            "[InitiatePesapalCheckout] Created pending payment %s for order %s",
            payment.payment_id, order_id
        )

        # 2. Submit to Pesapal — use payment.payment_id (PAY-XXXX) as merchant reference
        pesapal = PesapalHelper()
        submit_data = PesapalSubmitOrderDTO(
            merchant_reference=payment.payment_id,
            amount=amount,
            currency="USD",
            email=user_data.get("email", ""),
            phone=user_data.get("phone", ""),
            first_name=user_data.get("first_name", ""),
            last_name=user_data.get("last_name", ""),
            description=f"Payment {payment.payment_id} for Order #{user_data.get('order_number', order_id)}",
        )
        try:
            pesapal_resp = pesapal.submit_order(submit_data)
        except Exception as pesapal_exc:
            logger.error(
                "[InitiatePesapalCheckout] Pesapal submit_order failed for payment %s: %r",
                payment.payment_id, pesapal_exc
            )
            raise

        # 3. Store Pesapal tracking ID on the payment record
        update_dto = PaymentUpdateDTO(
            pesapal_tracking_id=pesapal_resp.order_tracking_id
        )
        updated_payment = self._repo.update(str(payment.id), update_dto)

        # 4. Create a PENDING transaction record for the audit trail
        try:
            self._repos.payment.transaction.create(TransactionCreateDTO(
                payment_id=str(updated_payment.id),
                type=TransactionType.PAYMENT,
                amount=amount,
                status=TransactionStatus.PENDING,
                reference=pesapal_resp.order_tracking_id,
            ))
        except Exception as tx_exc:
            logger.error(
                "[InitiatePesapalCheckout] Transaction record creation failed for payment %s: %r",
                updated_payment.payment_id, tx_exc
            )

        # 5. Audit log
        try:
            self._audit.activity_log.log(ActivityLogCreateDTO(
                action=Variables.PAYMENT_CREATE_ACTION,
                user_id=user_id,
                entity_type=Variables.PAYMENT_ENTITY_TYPE,
                entity_id=str(updated_payment.id),
                after=updated_payment,
                created_by=user_id,
                ip_address="system",
                user_agent="system",
            ))
        except Exception as audit_exc:
            logger.error(
                "[InitiatePesapalCheckout] Audit log failed for payment %s: %r",
                updated_payment.payment_id, audit_exc
            )

        # 6. Commit
        self._repos.payment.save()

        # 7. Emit event
        try:
            event_bus.emit("payment.pesapal_initiated", {
                "payment_id": str(updated_payment.id),
                "payment_ref": updated_payment.payment_id,
                "order_id": order_id,
                "user_id": user_id,
                "tracking_id": pesapal_resp.order_tracking_id,
                "amount": amount,
            })
        except Exception as event_exc:
            logger.error(
                "[InitiatePesapalCheckout] Event emit failed for payment %s: %r",
                updated_payment.payment_id, event_exc
            )

        logger.info(
            "[InitiatePesapalCheckout] Payment %s initiated via Pesapal. TrackingId=%s",
            updated_payment.payment_id, pesapal_resp.order_tracking_id
        )

        return {
            "redirect_url": pesapal_resp.redirect_url,
            "order_tracking_id": pesapal_resp.order_tracking_id,
            "payment_id": str(updated_payment.id),
            "payment_ref": updated_payment.payment_id,
        }


class HandlePesapalIpn:
    def __init__(self, repos: Repository) -> None:
        self._repos = repos

    def execute(
        self,
        tracking_id: str,
        status_result: PesapalTransactionStatusDTO,
    ) -> dict:
        status_desc = status_result.payment_status_description.lower().strip()
        logger.info(
            "[HandlePesapalIpn] Processing IPN for tracking_id=%s, status=%s",
            tracking_id, status_desc
        )

        if status_desc in ("completed", "success"):
            try:
                payment = self._repos.payment.payment.get_by_pesapal_tracking_id(tracking_id)
            except Exception as e:
                logger.warning(
                    "[HandlePesapalIpn] No payment found for tracking_id=%s: %r",
                    tracking_id, e
                )
                return {"status": "not_found", "tracking_id": tracking_id}

            # IDEMPOTENCY CHECK
            if payment.status == PaymentStatus.COMPLETED:
                logger.info(
                    "[HandlePesapalIpn] Payment %s already COMPLETED — idempotent IPN, skipping.",
                    payment.payment_id
                )
                return {"status": "already_completed", "payment_id": str(payment.id)}

            if payment.status not in (PaymentStatus.PENDING, PaymentStatus.PENDING_VERIFICATION):
                logger.warning(
                    "[HandlePesapalIpn] Payment %s is in unexpected state %s for IPN completion.",
                    payment.payment_id, payment.status
                )
                return {"status": "unexpected_state", "payment_id": str(payment.id)}

            try:
                result = AdminVerifyPayment(self._repos).execute(
                    payment_id=str(payment.id),
                    admin_id="system_pesapal",
                )
                logger.info(
                    "[HandlePesapalIpn] Payment %s auto-verified via IPN. Order activated.",
                    payment.payment_id
                )
                return {"status": "completed", "payment_id": str(result.id)}
            except Exception as verify_exc:
                logger.error(
                    "[HandlePesapalIpn] AdminVerifyPayment failed for payment %s: %r",
                    payment.payment_id, verify_exc
                )
                raise

        elif status_desc == "failed":
            try:
                payment = self._repos.payment.payment.get_by_pesapal_tracking_id(tracking_id)
            except Exception:
                logger.warning(
                    "[HandlePesapalIpn] No payment for failed IPN tracking_id=%s", tracking_id
                )
                return {"status": "not_found", "tracking_id": tracking_id}

            if payment.status == PaymentStatus.FAILED:
                return {"status": "already_failed", "payment_id": str(payment.id)}

            try:
                result = AdminRejectPayment(self._repos).execute(
                    payment_id=str(payment.id),
                    user_id="system_pesapal",
                    rejection_reason="Pesapal gateway reported payment as failed.",
                )
                return {"status": "failed", "payment_id": str(result.id)}
            except Exception as reject_exc:
                logger.error(
                    "[HandlePesapalIpn] AdminRejectPayment failed for payment %s: %r",
                    payment.payment_id, reject_exc
                )
                raise

        else:
            logger.info(
                "[HandlePesapalIpn] Status '%s' for tracking_id=%s — no action taken.",
                status_desc, tracking_id
            )
            return {"status": "pending", "tracking_id": tracking_id}