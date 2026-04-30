from typing import Optional, Any
from tuned.interface.audit.price_history import PriceHistoryService
from tuned.interface.audit.order_status_history import OrderStatusHistoryService
from tuned.interface.audit.activity_log import ActivityLogService
from tuned.interface.audit.email_log import EmailLogService

class AuditService:
    def __init__(self, repos: Any) -> None:
        self._repos = repos
        self._price_history: Optional[PriceHistoryService] = None
        self._order_status_history: Optional[OrderStatusHistoryService] = None
        self._activity_log: Optional[ActivityLogService] = None
        self._email_log: Optional[EmailLogService] = None

    @property
    def price_history(self) -> PriceHistoryService:
        if not self._price_history:
            self._price_history = PriceHistoryService(repos=self._repos)
        return self._price_history

    @property
    def order_status_history(self) -> OrderStatusHistoryService:
        if not self._order_status_history:
            self._order_status_history = OrderStatusHistoryService(repos=self._repos)
        return self._order_status_history

    @property
    def activity_log(self) -> ActivityLogService:
        if not self._activity_log:
            self._activity_log = ActivityLogService(repos=self._repos)
        return self._activity_log

    @property
    def email_log(self) -> EmailLogService:
        if not self._email_log:
            self._email_log = EmailLogService(repos=self._repos)
        return self._email_log

