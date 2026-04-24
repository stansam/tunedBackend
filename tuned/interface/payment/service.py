from __future__ import annotations

from tuned.interface.payment.payment import ProcessPayment, GetPaymentDetails, UpdatePaymentStatus
from tuned.interface.payment.invoice import GenerateInvoice, GetInvoiceDetails, MarkInvoicePaid
from tuned.interface.payment.discount import ApplyDiscount, CreateDiscount, GetDiscountDetails
from tuned.interface.payment.refund import ProcessRefund, ApproveRefund
from tuned.interface.payment.transaction import LogTransaction, GetTransactionHistory

class PaymentServiceManager:
    def __init__(self) -> None:
        self._process = ProcessPayment()
        self._get = GetPaymentDetails()
        self._update = UpdatePaymentStatus()

    def process(self, data) -> object:
        return self._process.execute(data)

    def get_details(self, payment_id: str) -> object:
        return self._get.execute(payment_id)

    def update_status(self, payment_id: str, data, actor_id: str) -> object:
        return self._update.execute(payment_id, data, actor_id)

class InvoiceServiceManager:
    def __init__(self) -> None:
        self._generate = GenerateInvoice()
        self._get = GetInvoiceDetails()
        self._mark_paid = MarkInvoicePaid()

    def generate(self, data) -> object:
        return self._generate.execute(data)

    def get_details(self, invoice_id: str) -> object:
        return self._get.execute(invoice_id)

    def mark_paid(self, invoice_id: str, payment_id: str, actor_id: str) -> object:
        return self._mark_paid.execute(invoice_id, payment_id, actor_id)

class DiscountServiceManager:
    def __init__(self) -> None:
        self._apply = ApplyDiscount()
        self._create = CreateDiscount()
        self._get = GetDiscountDetails()

    def apply(self, code: str, order_value: float) -> object:
        return self._apply.execute(code, order_value)

    def create(self, data, actor_id: str) -> object:
        return self._create.execute(data, actor_id)

    def get_details(self, discount_id: str) -> object:
        return self._get.execute(discount_id)

class RefundServiceManager:
    def __init__(self) -> None:
        self._process = ProcessRefund()
        self._approve = ApproveRefund()

    def process(self, data) -> object:
        return self._process.execute(data)

    def approve(self, refund_id: str, admin_id: str) -> object:
        return self._approve.execute(refund_id, admin_id)

class TransactionServiceManager:
    def __init__(self) -> None:
        self._log = LogTransaction()
        self._get_history = GetTransactionHistory()

    def log(self, data, actor_id: str) -> object:
        return self._log.execute(data, actor_id)

    def get_history(self, payment_id: str) -> list[object]:
        return self._get_history.execute(payment_id)
