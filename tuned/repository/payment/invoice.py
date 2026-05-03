from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from tuned.models import Invoice
from tuned.dtos.payment import InvoiceCreateDTO, InvoiceUpdateDTO, InvoiceResponseDTO
from tuned.repository.exceptions import DatabaseError, AlreadyExists, NotFound
from tuned.core.logging import get_logger

logger = get_logger(__name__)

class CreateInvoice:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, data: InvoiceCreateDTO) -> InvoiceResponseDTO:
        try:
            invoice = Invoice(
                order_id=data.order_id,
                user_id=data.user_id,
                subtotal=data.subtotal,
                total=data.total,
                due_date=data.due_date,
                payment_id=data.payment_id,
                discount=data.discount if data.discount is not None else 0.0,
                tax=data.tax if data.tax is not None else 0.0,
                paid=data.paid if data.paid is not None else False,
            )
            self.session.add(invoice)
            self.session.flush()
            return InvoiceResponseDTO.from_model(invoice)
        except IntegrityError as e:
            logger.error(f"[CreateInvoice] Integrity error: {e}")
            raise AlreadyExists("Invoice could not be created due to an integrity conflict.") from e
        except SQLAlchemyError as e:
            logger.error(f"[CreateInvoice] DB error: {e}")
            raise DatabaseError("Database error while creating invoice.") from e

class GetInvoiceByID:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, invoice_id: str) -> InvoiceResponseDTO:
        try:
            stmt = select(Invoice).where(Invoice.id == invoice_id)
            invoice = self.session.scalar(stmt)
            if not invoice:
                raise NotFound("Invoice not found.")
            return InvoiceResponseDTO.from_model(invoice)
        except SQLAlchemyError as e:
            logger.error(f"[GetInvoiceByID] DB error: {e}")
            raise DatabaseError("Database error while fetching invoice.") from e

class GetInvoiceByNumber:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, invoice_number: str) -> InvoiceResponseDTO:
        try:
            stmt = select(Invoice).where(Invoice.invoice_number == invoice_number)
            invoice = self.session.scalar(stmt)
            if not invoice:
                raise NotFound("Invoice not found.")
            return InvoiceResponseDTO.from_model(invoice)
        except SQLAlchemyError as e:
            logger.error(f"[GetInvoiceByNumber] DB error: {e}")
            raise DatabaseError("Database error while fetching invoice.") from e

class UpdateInvoice:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, invoice_id: str, data: InvoiceUpdateDTO) -> InvoiceResponseDTO:
        try:
            stmt = select(Invoice).where(Invoice.id == invoice_id)
            invoice = self.session.scalar(stmt)
            if not invoice:
                raise NotFound("Invoice not found.")
                
            if data.paid is not None:
                invoice.paid = data.paid
            if data.payment_id is not None:
                invoice.payment_id = data.payment_id
                
            self.session.flush()
            return InvoiceResponseDTO.from_model(invoice)
        except IntegrityError as e:
            logger.error(f"[UpdateInvoice] Integrity error: {e}")
            raise DatabaseError("Conflict updating invoice.") from e
        except SQLAlchemyError as e:
            logger.error(f"[UpdateInvoice] DB error: {e}")
            raise DatabaseError("Database error while updating invoice.") from e
