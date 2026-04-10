from sqlalchemy.orm import Session
from tuned.repository.audit.price_history import PriceHistoryRepository
from tuned.repository.audit.order_status_history import OrderStatusHistoryRepository
from tuned.repository.audit.activity_log import ActivityLogRepository
from tuned.repository.audit.email_log import EmailLogRepository
from tuned.extensions import db
class AuditRepository:
    def __init__(self) -> None:
        self.session = db.session
        self._price_history: PriceHistoryRepository | None = None
        self._order_status_history: OrderStatusHistoryRepository | None = None
        self._activity_log: ActivityLogRepository | None = None
        self._email_log: EmailLogRepository | None = None

    @property
    def price_history(self) -> PriceHistoryRepository:
        if not self._price_history:
            self._price_history = PriceHistoryRepository(self.session)
        return self._price_history

    @property
    def order_status_history(self) -> OrderStatusHistoryRepository:
        if not self._order_status_history:
            self._order_status_history = OrderStatusHistoryRepository(self.session)
        return self._order_status_history

    @property
    def activity_log(self) -> ActivityLogRepository:
        if not self._activity_log:
            self._activity_log = ActivityLogRepository(self.session)
        return self._activity_log

    @property
    def email_log(self) -> EmailLogRepository:
        if not self._email_log:
            self._email_log = EmailLogRepository(self.session)
        return self._email_log
