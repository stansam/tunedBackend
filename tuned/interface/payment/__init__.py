from __future__ import annotations

from tuned.interface.payment.service import (
    PaymentServiceManager,
    InvoiceServiceManager,
    DiscountServiceManager,
    RefundServiceManager,
    TransactionServiceManager,
    AcceptedMethodServiceManager
)

class PaymentService:
    def __init__(self) -> None:
        self._payment: PaymentServiceManager | None = None
        self._invoice: InvoiceServiceManager | None = None
        self._discount: DiscountServiceManager | None = None
        self._refund: RefundServiceManager | None = None
        self._transaction: TransactionServiceManager | None = None
        self._accepted_method: AcceptedMethodServiceManager | None = None

    @property
    def payment(self) -> PaymentServiceManager:
        if not self._payment:
            self._payment = PaymentServiceManager()
        return self._payment

    @property
    def invoice(self) -> InvoiceServiceManager:
        if not self._invoice:
            self._invoice = InvoiceServiceManager()
        return self._invoice

    @property
    def discount(self) -> DiscountServiceManager:
        if not self._discount:
            self._discount = DiscountServiceManager()
        return self._discount

    @property
    def refund(self) -> RefundServiceManager:
        if not self._refund:
            self._refund = RefundServiceManager()
        return self._refund

    @property
    def transaction(self) -> TransactionServiceManager:
        if not self._transaction:
            self._transaction = TransactionServiceManager()
        return self._transaction

    @property
    def accepted_method(self) -> AcceptedMethodServiceManager:
        if not self._accepted_method:
            self._accepted_method = AcceptedMethodServiceManager()
        return self._accepted_method

payment_service = PaymentService()
