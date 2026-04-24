from sqlalchemy.orm import Session
from tuned.dtos.payment import (
    PaymentCreateDTO, PaymentUpdateDTO, PaymentResponseDTO,
    InvoiceCreateDTO, InvoiceUpdateDTO, InvoiceResponseDTO,
    TransactionCreateDTO, TransactionResponseDTO,
    DiscountCreateDTO, DiscountUpdateDTO, DiscountResponseDTO,
    RefundCreateDTO, RefundUpdateDTO, RefundResponseDTO
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
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, data: PaymentCreateDTO) -> PaymentResponseDTO:
        return CreatePayment(self.db).execute(data)

    def get_by_id(self, payment_id: str) -> PaymentResponseDTO:
        return GetPaymentByID(self.db).execute(payment_id)

    def get_by_order_id(self, order_id: str) -> list[PaymentResponseDTO]:
        return GetPaymentByOrderID(self.db).execute(order_id)

    def update(self, payment_id: str, data: PaymentUpdateDTO) -> PaymentResponseDTO:
        return UpdatePayment(self.db).execute(payment_id, data)

    def get_spending_velocity(self, client_id: str, months: int = 6) -> list[tuple[str, float]]:
        return GetSpendingVelocity(self.db).execute(client_id, months)

class InvoiceManager:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, data: InvoiceCreateDTO) -> InvoiceResponseDTO:
        return CreateInvoice(self.db).execute(data)

    def get_by_id(self, invoice_id: str) -> InvoiceResponseDTO:
        return GetInvoiceByID(self.db).execute(invoice_id)

    def get_by_number(self, invoice_number: str) -> InvoiceResponseDTO:
        return GetInvoiceByNumber(self.db).execute(invoice_number)

    def update(self, invoice_id: str, data: InvoiceUpdateDTO) -> InvoiceResponseDTO:
        return UpdateInvoice(self.db).execute(invoice_id, data)

class TransactionManager:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, data: TransactionCreateDTO) -> TransactionResponseDTO:
        return CreateTransaction(self.db).execute(data)

    def get_by_id(self, transaction_id: str) -> TransactionResponseDTO:
        return GetTransactionByID(self.db).execute(transaction_id)

    def get_by_payment_id(self, payment_id: str) -> list[TransactionResponseDTO]:
        return GetTransactionsByPaymentID(self.db).execute(payment_id)

class DiscountManager:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, data: DiscountCreateDTO) -> DiscountResponseDTO:
        return CreateDiscount(self.db).execute(data)

    def get_by_id(self, discount_id: str) -> DiscountResponseDTO:
        return GetDiscountByID(self.db).execute(discount_id)

    def get_by_code(self, code: str) -> DiscountResponseDTO:
        return GetDiscountByCode(self.db).execute(code)

    def update(self, discount_id: str, data: DiscountUpdateDTO) -> DiscountResponseDTO:
        return UpdateDiscount(self.db).execute(discount_id, data)

    def increment_usage(self, discount_id: str) -> DiscountResponseDTO:
        return IncrementDiscountUsage(self.db).execute(discount_id)

class RefundManager:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, data: RefundCreateDTO) -> RefundResponseDTO:
        return CreateRefund(self.db).execute(data)

    def get_by_id(self, refund_id: str) -> RefundResponseDTO:
        return GetRefundByID(self.db).execute(refund_id)

    def update_status(self, refund_id: str, data: RefundUpdateDTO) -> RefundResponseDTO:
        return UpdateRefundStatus(self.db).execute(refund_id, data)

class AcceptedMethodRepositoryManager:
    def __init__(self, db: Session) -> None:
        self.db = db
        self._repo = AcceptedPaymentMethodRepository(self.db)

    def create(self, data) -> object:
        return self._repo.create(data)

    def update(self, method_id: str, data) -> object:
        return self._repo.update(method_id, data)

    def get_by_id(self, method_id: str) -> object:
        return self._repo.get_by_id(method_id)

    def get_all_active(self) -> list:
        return self._repo.get_all_active()