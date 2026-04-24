from __future__ import annotations
import logging
from tuned.core.logging import get_logger
from tuned.dtos.audit import ActivityLogCreateDTO
from tuned.dtos.payment import InvoiceCreateDTO, InvoiceUpdateDTO, InvoiceResponseDTO
from tuned.interface.audit import audit_service
from tuned.repository import repositories
from tuned.utils.variables import Variables
from tuned.core.events import get_event_bus

logger: logging.Logger = get_logger(__name__)

class GenerateInvoice:
    def execute(self, data: InvoiceCreateDTO) -> InvoiceResponseDTO:
        try:
            invoice = repositories.payment.invoice.create(data)

            try:
                audit_service.activity_log.log(ActivityLogCreateDTO(
                    action=Variables.INVOICE_CREATE_ACTION,
                    user_id=data.user_id,
                    entity_type=Variables.INVOICE_ENTITY_TYPE,
                    entity_id=invoice.id,
                    after={"invoice_number": invoice.invoice_number, "total": invoice.total},
                    created_by=data.user_id,
                ))
            except Exception as audit_exc:
                logger.error(f"[GenerateInvoice] Audit failed for invoice {invoice.id}: {audit_exc!r}")

            try:
                get_event_bus().emit("invoice.created", {
                    "invoice_id": invoice.id,
                    "order_id": invoice.order_id,
                    "user_id": invoice.user_id,
                })
            except Exception as event_exc:
                logger.error(f"[GenerateInvoice] Event emit failed for invoice {invoice.id}: {event_exc!r}")

            logger.info(f"[GenerateInvoice] Generated invoice {invoice.invoice_number} for user {data.user_id}")
            return invoice
        except Exception as exc:
            logger.error(f"[GenerateInvoice] Failed to generate invoice: {exc!r}")
            raise

class GetInvoiceDetails:
    def execute(self, invoice_id: str) -> InvoiceResponseDTO:
        try:
            return repositories.payment.invoice.get_by_id(invoice_id)
        except Exception as exc:
            logger.error(f"[GetInvoiceDetails] Failed to get invoice {invoice_id}: {exc!r}")
            raise

class MarkInvoicePaid:
    def execute(self, invoice_id: str, payment_id: str, actor_id: str) -> InvoiceResponseDTO:
        try:
            data = InvoiceUpdateDTO(paid=True, payment_id=payment_id)
            invoice = repositories.payment.invoice.update(invoice_id, data)

            try:
                audit_service.activity_log.log(ActivityLogCreateDTO(
                    action=Variables.INVOICE_UPDATE_ACTION,
                    user_id=invoice.user_id,
                    entity_type=Variables.INVOICE_ENTITY_TYPE,
                    entity_id=invoice.id,
                    after={"paid": invoice.paid, "payment_id": invoice.payment_id},
                    created_by=actor_id,
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
