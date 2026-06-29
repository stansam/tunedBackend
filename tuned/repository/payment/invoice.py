from uuid import UUID
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
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
                order_id=UUID(data.order_id),
                user_id=UUID(data.user_id),
                subtotal=data.subtotal,
                total=data.total,
                due_date=data.due_date,
                payment_id=UUID(data.payment_id) if data.payment_id else None,
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
                invoice.payment_id = UUID(data.payment_id)
                
            self.session.flush()
            return InvoiceResponseDTO.from_model(invoice)
        except IntegrityError as e:
            logger.error(f"[UpdateInvoice] Integrity error: {e}")
            raise DatabaseError("Conflict updating invoice.") from e
        except SQLAlchemyError as e:
            logger.error(f"[UpdateInvoice] DB error: {e}")
            raise DatabaseError("Database error while updating invoice.") from e

class GetInvoiceByPaymentID:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, payment_id: str) -> InvoiceResponseDTO:
        try:
            stmt = select(Invoice).where(Invoice.payment_id == UUID(payment_id))
            invoice = self.session.scalar(stmt)
            if not invoice:
                raise NotFound("Invoice not found for this payment.")
            return InvoiceResponseDTO.from_model(invoice)
        except SQLAlchemyError as e:
            logger.error(f"[GetInvoiceByPaymentID] DB error: {e}")
            raise DatabaseError("Database error while fetching invoice by payment ID.") from e


class GetInvoiceByOrderId:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, order_id: str) -> Optional[InvoiceResponseDTO]:
        try:
            stmt = select(Invoice).where(Invoice.order_id == UUID(order_id))
            invoice = self.session.scalar(stmt)
            if not invoice:
                return None
            return InvoiceResponseDTO.from_model(invoice)
        except SQLAlchemyError as e:
            logger.error("[GetInvoiceByOrderId] DB error: %s", e)
            raise DatabaseError("Database error while fetching invoice for order.") from e


class ListInvoicesByUser:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, user_id: str, page: int = 1, per_page: int = 10) -> tuple[list[InvoiceResponseDTO], int]:
        try:
            base_stmt = select(Invoice).where(Invoice.user_id == UUID(user_id))
            count_stmt = select(func.count()).select_from(base_stmt.subquery())
            total = self.session.scalar(count_stmt) or 0

            paginated_stmt = (
                base_stmt
                .order_by(Invoice.created_at.desc())
                .offset((page - 1) * per_page)
                .limit(per_page)
            )
            invoices = self.session.scalars(paginated_stmt).all()
            return [InvoiceResponseDTO.from_model(i) for i in invoices], total
        except SQLAlchemyError as e:
            logger.error("[ListInvoicesByUser] DB error: %s", e)
            raise DatabaseError("Database error while listing invoices for user.") from e
