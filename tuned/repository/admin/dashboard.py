from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from tuned.models import Order, User, Payment, OrderDeadlineExtensionRequest, Service, ActivityLog
from tuned.models.enums import OrderStatus, PaymentStatus, ExtensionRequestStatus
from tuned.dtos.order import derive_priority
from tuned.dtos.admin.dashboard import (
    AdminKPIDTO, AdminDashboardAnalyticsDTO,
    AdminDashboardTrackingDTO, AdminDashboardAlertsDTO,
    ActionableAlertDTO, SpendingVelocityDTO, ChartDataDTO,
    AdminUpcomingDeadlineDTO, AdminActivityFeedEntryDTO,
)
from tuned.core.exceptions import DatabaseError
from tuned.core.logging import get_logger

logger = get_logger(__name__)
_ACTIVE = (OrderStatus.PENDING, OrderStatus.ACTIVE, OrderStatus.REVISION)


class GetAdminKPIs:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self) -> AdminKPIDTO:
        try:
            active_orders = self.session.scalar(
                select(func.count(Order.id)).where(
                    Order.status.in_(_ACTIVE),
                    Order.is_deleted == False
                )
            ) or 0

            # Total revenue: sum of all completed payments
            total_revenue = float(self.session.scalar(
                select(func.coalesce(func.sum(Payment.amount), 0))
                .where(
                    Payment.status == PaymentStatus.COMPLETED,
                    Payment.is_deleted == False
                )
            ) or 0)

            total_clients = self.session.scalar(
                select(func.count(User.id)).where(
                    User.is_admin == False,
                    User.is_deleted == False
                )
            ) or 0

            pending_review = self.session.scalar(
                select(func.count(Order.id)).where(
                    Order.status == OrderStatus.COMPLETED_PENDING_REVIEW,
                    Order.is_deleted == False
                )
            ) or 0

            # Count of pending extension requests
            pending_extensions = self.session.scalar(
                select(func.count(OrderDeadlineExtensionRequest.id)).where(
                    OrderDeadlineExtensionRequest.status == ExtensionRequestStatus.PENDING,
                    OrderDeadlineExtensionRequest.is_deleted == False
                )
            ) or 0

            pending_actions = pending_review + pending_extensions

            return AdminKPIDTO(
                active_orders=active_orders,
                total_revenue=total_revenue,
                total_clients=total_clients,
                pending_actions=pending_actions,
            )
        except Exception as exc:
            logger.error("[GetAdminKPIs] %s", exc)
            raise DatabaseError(str(exc)) from exc


def _month_label_expr(session: Session, column: Any) -> Any:
    try:
        dialect_name = session.get_bind().dialect.name
    except Exception:
        dialect_name = "postgresql"
    if dialect_name == "sqlite":
        return func.strftime("%Y-%m", column)
    return func.to_char(column, "YYYY-MM")


class GetAdminAnalytics:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self) -> AdminDashboardAnalyticsDTO:
        try:
            # Spending velocity: monthly payment sums (last 6 months)
            six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
            month_expr = _month_label_expr(self.session, Payment.created_at)
            vel_rows = self.session.execute(
                select(
                    month_expr.label("month"),
                    func.sum(Payment.amount).label("amount"),
                )
                .where(
                    Payment.status == PaymentStatus.COMPLETED,
                    Payment.created_at >= six_months_ago,
                    Payment.is_deleted == False
                )
                .group_by("month")
                .order_by("month")
            ).all()
            spending_velocity = [
                SpendingVelocityDTO(month=r.month, amount=float(r.amount))
                for r in vel_rows
            ]

            # Project lifecycle: order count by status
            lifecycle_rows = self.session.execute(
                select(Order.status, func.count(Order.id))
                .where(Order.is_deleted == False)
                .group_by(Order.status)
            ).all()
            project_lifecycle = [
                ChartDataDTO(name=status.value, value=count)
                for status, count in lifecycle_rows
            ]

            # Service mix: order count by service name
            mix_rows = self.session.execute(
                select(Service.name, func.count(Order.id))
                .join(Order, Order.service_id == Service.id)
                .where(
                    Order.is_deleted == False,
                    Service.is_deleted == False
                )
                .group_by(Service.name)
            ).all()
            service_mix = [
                ChartDataDTO(name=name, value=count)
                for name, count in mix_rows
            ]

            # Referral growth: new (non-admin) users per month (last 6 months)
            user_month_expr = _month_label_expr(self.session, User.created_at)
            ref_rows = self.session.execute(
                select(
                    user_month_expr.label("month"),
                    func.count(User.id).label("value"),
                )
                .where(
                    User.is_admin == False,
                    User.created_at >= six_months_ago,
                    User.is_deleted == False
                )
                .group_by("month")
                .order_by("month")
            ).all()
            referral_growth = [
                ChartDataDTO(name=r.month, value=r.value) for r in ref_rows
            ]

            return AdminDashboardAnalyticsDTO(
                spending_velocity=spending_velocity,
                project_lifecycle=project_lifecycle,
                service_mix=service_mix,
                referral_growth=referral_growth,
            )

        except Exception as exc:
            logger.error("[GetAdminAnalytics] %s", exc)
            raise DatabaseError(str(exc)) from exc


class GetAdminTracking:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, limit: int = 5) -> AdminDashboardTrackingDTO:
        try:
            upcoming = self.session.scalars(
                select(Order)
                .where(
                    Order.status.in_(_ACTIVE),
                    Order.due_date.isnot(None),
                    Order.is_deleted == False
                )
                .order_by(Order.due_date.asc())
                .limit(limit)
            ).all()

            deadlines = [
                AdminUpcomingDeadlineDTO(
                    id=str(o.id),
                    order_number=o.order_number,
                    title=o.title,
                    due_date=o.due_date.isoformat() if o.due_date else "",
                    priority=derive_priority(o.due_date).name,
                )
                for o in upcoming
            ]

            # Activity feed: last 20 audit log entries (global)
            feed_rows = self.session.scalars(
                select(ActivityLog)
                .where(ActivityLog.is_deleted == False)
                .order_by(ActivityLog.created_at.desc())
                .limit(20)
            ).all()

            activity_feed = [
                AdminActivityFeedEntryDTO(
                    id=str(row.id),
                    action=row.action or "",
                    entity_type=row.entity_type or "",
                    entity_id=str(row.entity_id) if row.entity_id else "",
                    created_at=row.created_at.isoformat() if row.created_at else "",
                )
                for row in feed_rows
            ]

            return AdminDashboardTrackingDTO(
                upcoming_deadlines=deadlines,
                activity_feed=activity_feed,
            )
        except Exception as exc:
            logger.error("[GetAdminTracking] %s", exc)
            raise DatabaseError(str(exc)) from exc


class GetAdminAlerts:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, limit: int = 10) -> AdminDashboardAlertsDTO:
        try:
            alerts: list[ActionableAlertDTO] = []

            # Pending review orders
            pending_review_orders = self.session.scalars(
                select(Order)
                .where(
                    Order.status == OrderStatus.COMPLETED_PENDING_REVIEW,
                    Order.is_deleted == False
                )
                .order_by(Order.updated_at.desc())
                .limit(limit)
            ).all()
            for o in pending_review_orders:
                alerts.append(ActionableAlertDTO(
                    id=str(o.id),
                    type="PENDING_REVIEW",
                    message=f"Order {o.order_number} is awaiting your review.",
                    metadata={"order_number": o.order_number},
                    created_at=o.updated_at.isoformat() if o.updated_at else "",
                ))

            # Extension requests
            extensions = self.session.scalars(
                select(OrderDeadlineExtensionRequest)
                .where(
                    OrderDeadlineExtensionRequest.status == ExtensionRequestStatus.PENDING,
                    OrderDeadlineExtensionRequest.is_deleted == False
                )
                .order_by(OrderDeadlineExtensionRequest.requested_at.desc())
                .limit(limit)
            ).all()
            for ext in extensions:
                alerts.append(ActionableAlertDTO(
                    id=str(ext.id),
                    type="EXTENSION_REQUEST",
                    message=f"Extension request for order {ext.order.order_number}.",
                    metadata={"order_id": str(ext.order_id)},
                    created_at=ext.requested_at.isoformat() if ext.requested_at else "",
                ))

            alerts.sort(key=lambda a: a.created_at, reverse=True)
            return AdminDashboardAlertsDTO(alerts=alerts[:limit])
        except Exception as exc:
            logger.error("[GetAdminAlerts] %s", exc)
            raise DatabaseError(str(exc)) from exc
