from sqlalchemy.orm import Session
from typing import Optional
from tuned.models.order import Order
from tuned.models.revision_request import OrderRevisionRequest
from tuned.models.deadline_extension import OrderDeadlineExtensionRequest
from tuned.models.enums import RevisionRequestStatus, Priority
from tuned.dtos.admin import AdminOrderListResponseDTO, AdminOrdersStatsResponseDTO
from tuned.dtos import OrderListRequestDTO
from tuned.dtos.payment import AdminPaymentResponseDTO
from tuned.dtos.admin import(
    AdminDashboardAnalyticsDTO, AdminDashboardTrackingDTO,
    AdminDashboardAlertsDTO, AdminKPIDTO,
    AdminUserListRequestDTO, AdminUserListResponseDTO,
    AdminUserStatsDTO, GeographicDistributionDTO
)
from tuned.repository.admin.dashboard import (
    GetAdminKPIs, GetAdminAnalytics, GetAdminTracking, GetAdminAlerts
)

from tuned.repository.admin.orders import (
    GetAllOrders, GetAdminOrdersStats, ActivateOrder, EscalateOrder,
    GetOrderRevisionRequests, UpdateRevisionRequestStatus,
    GetDeadlineExtensionRequests, CreateDeadlineExtensionRequest
)

from tuned.repository.admin.users import (
    GetAdminUserList, GetAdminUserStats, GetGeographicDistribution
)

class AdminAnalyticsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_kpis(self) -> AdminKPIDTO:
        return GetAdminKPIs(session=self.session).execute()

    def get_analytics(self) -> AdminDashboardAnalyticsDTO:
        return GetAdminAnalytics(session=self.session).execute()

    def get_tracking(self, limit: int = 5) -> AdminDashboardTrackingDTO:
        return GetAdminTracking(session=self.session).execute(limit)
    
    def get_alerts(self, limit: int = 10) -> AdminDashboardAlertsDTO:
        return GetAdminAlerts(session=self.session).execute(limit)

class AdminOrderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_all_orders(self, req: OrderListRequestDTO) -> AdminOrderListResponseDTO:
        return GetAllOrders(self.session).execute(req)
    
    def get_admin_order_stats(self) -> AdminOrdersStatsResponseDTO:
        return GetAdminOrdersStats(self.session).execute()
    
    def activate_order(self, order_id: str) -> Order:
        return ActivateOrder(self.session).execute(order_id)
    
    def escalate_order(self, order_id: str) -> Order:
        return EscalateOrder(self.session).execute(order_id)

    def get_revision_requests(self, order_id: str) -> list[OrderRevisionRequest]:
        return GetOrderRevisionRequests(self.session).execute(order_id)

    def update_revision_status(
        self, request_id: str, reviewed_by: str,
        new_status: RevisionRequestStatus, internal_notes: Optional[str] = None
    ) -> OrderRevisionRequest:
        return UpdateRevisionRequestStatus(self.session).execute(
            request_id, reviewed_by, new_status, internal_notes
        )

    def get_deadline_extensions(self, order_id: str) -> list[OrderDeadlineExtensionRequest]:
        return GetDeadlineExtensionRequests(self.session).execute(order_id)

    def create_deadline_extension(
        self, order_id: str, requested_by: str,
        requested_hours: int, reason: str, priority: Priority
    ) -> OrderDeadlineExtensionRequest:
        return CreateDeadlineExtensionRequest(self.session).execute(
            order_id, requested_by, requested_hours, reason, priority
        )

class AdminUserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_users(self, req: AdminUserListRequestDTO) -> AdminUserListResponseDTO:
        return GetAdminUserList(self.session).execute(req)

    def get_stats(self) -> AdminUserStatsDTO:
        return GetAdminUserStats(self.session).execute()

    def get_geography(self) -> list[GeographicDistributionDTO]:
        return GetGeographicDistribution(self.session).execute()


class AdminPaymentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_payments(
        self,
        status: Optional[str] = None,
        q: Optional[str] = None,
        page: int = 1,
        per_page: int = 10
    ) -> tuple[list[AdminPaymentResponseDTO], int]:
        from tuned.repository.admin.payments import GetAdminPaymentsList
        return GetAdminPaymentsList(self.session).execute(
            status=status, q=q, page=page, per_page=per_page
        )


__all__ = [
    "AdminAnalyticsRepository",
    "AdminOrderRepository",
    "AdminUserRepository",
    "AdminPaymentRepository",
]