from sqlalchemy.orm import Session
from tuned.dtos.payment import (
    PaymentCreateDTO, PaymentUpdateDTO, PaymentResponseDTO,
    InvoiceCreateDTO, InvoiceUpdateDTO, InvoiceResponseDTO,
    TransactionCreateDTO, TransactionResponseDTO,
    DiscountCreateDTO, DiscountUpdateDTO, DiscountResponseDTO,
    RefundCreateDTO, RefundUpdateDTO, RefundResponseDTO,
    AcceptedMethodCreateDTO, AcceptedMethodUpdateDTO, AcceptedMethodResponseDTO
)

from tuned.repository.payment.payment import (
    CreatePayment, GetPaymentByID, GetPaymentByOrderID, UpdatePayment, GetSpendingVelocity
)
from tuned.repository.payment.invoice import (
    CreateInvoice, GetInvoiceByID, GetInvoiceByNumber, UpdateInvoice
)
from tuned.repository.payment.transaction import (
    CreateTransaction, GetTransactionByID, GetTransactionsByPaymentID
)
from tuned.repository.payment.discount import (
    CreateDiscount, GetDiscountByID, GetDiscountByCode, UpdateDiscount, IncrementDiscountUsage
)
from tuned.repository.payment.refund import (
    CreateRefund, GetRefundByID, UpdateRefundStatus
)
from tuned.repository.payment.accepted_method import AcceptedPaymentMethodRepository

class PaymentsManager:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: PaymentCreateDTO) -> PaymentResponseDTO:
        return CreatePayment(self.session).execute(data)

    def get_by_id(self, payment_id: str) -> PaymentResponseDTO:
        return GetPaymentByID(self.session).execute(payment_id)

    def get_by_order_id(self, order_id: str) -> list[PaymentResponseDTO]:
        return GetPaymentByOrderID(self.session).execute(order_id)

    def update(self, payment_id: str, data: PaymentUpdateDTO) -> PaymentResponseDTO:
        return UpdatePayment(self.session).execute(payment_id, data)

    def get_spending_velocity(self, client_id: str, months: int = 6) -> list[tuple[str, float]]:
        return GetSpendingVelocity(self.session).execute(client_id, months)

class InvoiceManager:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: InvoiceCreateDTO) -> InvoiceResponseDTO:
        return CreateInvoice(self.session).execute(data)

    def get_by_id(self, invoice_id: str) -> InvoiceResponseDTO:
        return GetInvoiceByID(self.session).execute(invoice_id)

    def get_by_number(self, invoice_number: str) -> InvoiceResponseDTO:
        return GetInvoiceByNumber(self.session).execute(invoice_number)

    def update(self, invoice_id: str, data: InvoiceUpdateDTO) -> InvoiceResponseDTO:
        return UpdateInvoice(self.session).execute(invoice_id, data)

class TransactionManager:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: TransactionCreateDTO) -> TransactionResponseDTO:
        return CreateTransaction(self.session).execute(data)

    def get_by_id(self, transaction_id: str) -> TransactionResponseDTO:
        return GetTransactionByID(self.session).execute(transaction_id)

    def get_by_payment_id(self, payment_id: str) -> list[TransactionResponseDTO]:
        return GetTransactionsByPaymentID(self.session).execute(payment_id)

class DiscountManager:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: DiscountCreateDTO) -> DiscountResponseDTO:
        return CreateDiscount(self.session).execute(data)

    def get_by_id(self, discount_id: str) -> DiscountResponseDTO:
        return GetDiscountByID(self.session).execute(discount_id)

    def get_by_code(self, code: str) -> DiscountResponseDTO:
        return GetDiscountByCode(self.session).execute(code)

    def update(self, discount_id: str, data: DiscountUpdateDTO) -> DiscountResponseDTO:
        return UpdateDiscount(self.session).execute(discount_id, data)

    def increment_usage(self, discount_id: str) -> DiscountResponseDTO:
        return IncrementDiscountUsage(self.session).execute(discount_id)

class RefundManager:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: RefundCreateDTO) -> RefundResponseDTO:
        return CreateRefund(self.session).execute(data)

    def get_by_id(self, refund_id: str) -> RefundResponseDTO:
        return GetRefundByID(self.session).execute(refund_id)

    def update_status(self, refund_id: str, data: RefundUpdateDTO) -> RefundResponseDTO:
        return UpdateRefundStatus(self.session).execute(refund_id, data)

class AcceptedMethodRepositoryManager:
    def __init__(self, session: Session) -> None:
        self.session = session
        self._repo = AcceptedPaymentMethodRepository(self.session)

    def create(self, data: AcceptedMethodCreateDTO) -> AcceptedMethodResponseDTO:
        return self._repo.create(data)

    def update(self, method_id: str, data: AcceptedMethodUpdateDTO) -> AcceptedMethodResponseDTO:
        return self._repo.update(method_id, data)

    def get_by_id(self, method_id: str) -> AcceptedMethodResponseDTO:
        return self._repo.get_by_id(method_id)

    def get_all_active(self) -> list[AcceptedMethodResponseDTO]:
        return self._repo.get_all_active()