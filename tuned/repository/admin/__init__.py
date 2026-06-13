from sqlalchemy.orm import Session
from tuned.models.order import Order
from tuned.dtos.admin import AdminOrderListResponseDTO, AdminOrdersStatsResponseDTO
from tuned.dtos import OrderListRequestDTO
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
    GetAllOrders, GetAdminOrdersStats, ActivateOrder, EscalateOrder
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

class AdminUserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_users(self, req: AdminUserListRequestDTO) -> AdminUserListResponseDTO:
        return GetAdminUserList(self.session).execute(req)

    def get_stats(self) -> AdminUserStatsDTO:
        return GetAdminUserStats(self.session).execute()

    def get_geography(self) -> list[GeographicDistributionDTO]:
        return GetGeographicDistribution(self.session).execute()
    
__all__ = [
    "AdminAnalyticsRepository",
    "AdminOrderRepository",
    "AdminUserRepository",
]