from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from tuned.interface.payment.payment import ProcessPayment, GetPaymentDetails, ClientMarkAsPaid, AdminVerifyPayment
from tuned.interface.payment.invoice import GenerateInvoice, GetInvoiceDetails, MarkInvoicePaid
from tuned.interface.payment.discount import ApplyDiscount, CreateDiscount, GetDiscountDetails
from tuned.interface.payment.refund import ProcessRefund, ApproveRefund
from tuned.interface.payment.transaction import LogTransaction, GetTransactionHistory
from tuned.interface.payment.accepted_method import AdminCreateAcceptedMethod, AdminUpdateAcceptedMethod, GetAcceptedMethods

if TYPE_CHECKING:
    from tuned.repository import Repository

class PaymentServiceManager:
    def __init__(self, repos: Optional[Repository] = None) -> None:
        self._process = ProcessPayment(repos=repos)
        self._get = GetPaymentDetails(repos=repos)
        self._mark_paid_client = ClientMarkAsPaid(repos=repos)
        self._verify_payment = AdminVerifyPayment(repos=repos)

    def process(self, data) -> object:
        return self._process.execute(data)

    def get_details(self, payment_id: str) -> object:
        return self._get.execute(payment_id)

    def mark_as_paid_client(self, payment_id: str, client_proof_reference: str, client_id: str) -> object:
        return self._mark_paid_client.execute(payment_id, client_proof_reference, client_id)

    def verify_payment(self, payment_id: str, admin_id: str) -> object:
        return self._verify_payment.execute(payment_id, admin_id)

class AcceptedMethodServiceManager:
    def __init__(self, repos: Optional[Repository] = None) -> None:
        self._create = AdminCreateAcceptedMethod(repos=repos)
        self._update = AdminUpdateAcceptedMethod(repos=repos)
        self._get_all = GetAcceptedMethods(repos=repos)

    def create(self, data, admin_id: str) -> object:
        return self._create.execute(data, admin_id)

    def update(self, method_id: str, data, admin_id: str) -> object:
        return self._update.execute(method_id, data, admin_id)

    def get_all(self) -> list[object]:
        return self._get_all.execute()

class InvoiceServiceManager:
    def __init__(self, repos: Optional[Repository] = None) -> None:
        self._generate = GenerateInvoice(repos=repos)
        self._get = GetInvoiceDetails(repos=repos)
        self._mark_paid = MarkInvoicePaid(repos=repos)

    def generate(self, data) -> object:
        return self._generate.execute(data)

    def get_details(self, invoice_id: str) -> object:
        return self._get.execute(invoice_id)

    def mark_paid(self, invoice_id: str, payment_id: str, actor_id: str) -> object:
        return self._mark_paid.execute(invoice_id, payment_id, actor_id)

class DiscountServiceManager:
    def __init__(self, repos: Optional[Repository] = None) -> None:
        self._apply = ApplyDiscount(repos=repos)
        self._create = CreateDiscount(repos=repos)
        self._get = GetDiscountDetails(repos=repos)

    def apply(self, code: str, order_value: float, user_id: str) -> object:
        return self._apply.execute(code, order_value, user_id)

    def create(self, data, actor_id: str) -> object:
        return self._create.execute(data, actor_id)

    def get_details(self, discount_id: str) -> object:
        return self._get.execute(discount_id)

class RefundServiceManager:
    def __init__(self, repos: Optional[Repository] = None) -> None:
        self._process = ProcessRefund(repos=repos)
        self._approve = ApproveRefund(repos=repos)

    def process(self, data) -> object:
        return self._process.execute(data)

    def approve(self, refund_id: str, admin_id: str) -> object:
        return self._approve.execute(refund_id, admin_id)

class TransactionServiceManager:
    def __init__(self, repos: Optional[Repository] = None) -> None:
        self._log = LogTransaction(repos=repos)
        self._get_history = GetTransactionHistory(repos=repos)

    def log(self, data, actor_id: str) -> object:
        return self._log.execute(data, actor_id)

    def get_history(self, payment_id: str) -> list[object]:
        return self._get_history.execute(payment_id)
