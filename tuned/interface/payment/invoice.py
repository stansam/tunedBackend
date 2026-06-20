from __future__ import annotations
import logging
from typing import Optional, TYPE_CHECKING
from tuned.core.logging import get_logger
from tuned.dtos.audit import ActivityLogCreateDTO
from tuned.dtos.payment import InvoiceCreateDTO, InvoiceUpdateDTO, InvoiceResponseDTO
from tuned.utils.variables import Variables
from tuned.core.events import get_event_bus

if TYPE_CHECKING:
    from tuned.repository import Repository

logger: logging.Logger = get_logger(__name__)

class GenerateInvoice:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.payment.invoice
        self._repos = repos
        from tuned.interface.audit import AuditService
        self._audit = AuditService(repos=repos)

    def execute(self, data: InvoiceCreateDTO) -> InvoiceResponseDTO:
        try:
            invoice = self._repo.create(data)

            try:
                self._audit.activity_log.log(ActivityLogCreateDTO(
                    action=Variables.INVOICE_CREATE_ACTION,
                    user_id=data.user_id,
                    entity_type=Variables.INVOICE_ENTITY_TYPE,
                    entity_id=invoice.id,
                    after={"invoice_number": invoice.invoice_number, "total": invoice.total},
                    created_by=data.user_id,
                    ip_address="system",
                    user_agent="system"
                ))
            except Exception as audit_exc:
                logger.error("[GenerateInvoice] Audit failed for invoice %s: %r", invoice.id, audit_exc)

            try:
                order = self._repos.order.get_by_id(str(invoice.order_id))
                client = self._repos.user.get_user_by_id(str(invoice.user_id))

                # Email notification
                try:
                    from tuned.services.email_service import send_invoice_created_email
                    send_invoice_created_email(client, invoice, order.order_number)
                except Exception as email_exc:
                    logger.error("[GenerateInvoice] Email notification failed: %r", email_exc)

                get_event_bus().emit("invoice.created", {
                    "invoice_id":     str(invoice.id),
                    "invoice_number": invoice.invoice_number,
                    "order_id":       str(invoice.order_id),
                    "order_number":   order.order_number,
                    "user_id":        str(invoice.user_id),
                    "client_name":    client.get_name(),
                    "client_email":   client.email,
                    "total":          float(invoice.total),
                })
            except Exception as event_exc:
                logger.error("[GenerateInvoice] Event emit failed for invoice %s: %r", invoice.id, event_exc)

            logger.info("[GenerateInvoice] Generated invoice %s for user %s", invoice.invoice_number, data.user_id)
            return invoice
        except Exception as exc:
            logger.error(f"[GenerateInvoice] Failed to generate invoice: {exc!r}")
            raise

class GetInvoiceDetails:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.payment.invoice

    def execute(self, invoice_id: str) -> InvoiceResponseDTO:
        try:
            return self._repo.get_by_id(invoice_id)
        except Exception as exc:
            logger.error(f"[GetInvoiceDetails] Failed to get invoice {invoice_id}: {exc!r}")
            raise

class MarkInvoicePaid:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.payment.invoice
        from tuned.interface.audit import AuditService
        self._audit = AuditService(repos=repos)

    def execute(self, invoice_id: str, payment_id: str, actor_id: str) -> InvoiceResponseDTO:
        try:
            data = InvoiceUpdateDTO(paid=True, payment_id=payment_id)
            invoice = self._repo.update(invoice_id, data)

            try:
                self._audit.activity_log.log(ActivityLogCreateDTO(
                    action=Variables.INVOICE_UPDATE_ACTION,
                    user_id=invoice.user_id,
                    entity_type=Variables.INVOICE_ENTITY_TYPE,
                    entity_id=invoice.id,
                    after={"paid": invoice.paid, "payment_id": invoice.payment_id},
                    created_by=actor_id,
                    ip_address="system",
                    user_agent="system"
                ))
            except Exception as audit_exc:
                logger.error(f"[MarkInvoicePaid] Audit failed for invoice {invoice.id}: {audit_exc!r}")
                
            try:
                get_event_bus().emit("invoice.paid", {
                    "invoice_id": invoice.id,
                    "payment_id": payment_id,
                    "user_id": invoice.user_id,
                })
            except Exception as event_exc:
                logger.error(f"[MarkInvoicePaid] Event emit failed for invoice {invoice.id}: {event_exc!r}")

            logger.info(f"[MarkInvoicePaid] Invoice {invoice.invoice_number} marked as paid")
            return invoice
        except Exception as exc:
            logger.error(f"[MarkInvoicePaid] Failed to update invoice {invoice_id}: {exc!r}")
            raise
