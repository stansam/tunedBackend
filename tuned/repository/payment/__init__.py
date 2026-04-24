from typing import Optional
from tuned.extensions import db
from tuned.repository.payment.repository import (
    PaymentsManager,
    InvoiceManager,
    TransactionManager,
    DiscountManager,
    RefundManager,
    AcceptedMethodRepositoryManager
)

class PaymentRepository:
    def __init__(self):
        self._db = db
        self._payment: Optional[PaymentsManager] = None
        self._invoice: Optional[InvoiceManager] = None
        self._transaction: Optional[TransactionManager] = None
        self._discount: Optional[DiscountManager] = None
        self._refund: Optional[RefundManager] = None
        self._accepted_method: Optional[AcceptedMethodRepositoryManager] = None

    @property
    def payment(self) -> PaymentsManager:
        if not self._payment:
            self._payment = PaymentsManager(self._db.session)
        return self._payment

    @property
    def invoice(self) -> InvoiceManager:
        if not self._invoice:
            self._invoice = InvoiceManager(self._db.session)
        return self._invoice

    @property
    def transaction(self) -> TransactionManager:
        if not self._transaction:
            self._transaction = TransactionManager(self._db.session)
        return self._transaction

    @property
    def discount(self) -> DiscountManager:
        if not self._discount:
            self._discount = DiscountManager(self._db.session)
        return self._discount

    @property
    def refund(self) -> RefundManager:
        if not self._refund:
            self._refund = RefundManager(self._db.session)
        return self._refund

    @property
    def accepted_method(self) -> AcceptedMethodRepositoryManager:
        if not self._accepted_method:
            self._accepted_method = AcceptedMethodRepositoryManager(self._db.session)
        return self._accepted_method