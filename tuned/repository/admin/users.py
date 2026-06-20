from __future__ import annotations
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, desc, asc, or_
from tuned.models import User, Order
from tuned.models.enums import OrderStatus, PaymentStatus
from tuned.dtos.admin.users import (
    AdminUserInsightDTO, AdminUserListResponseDTO,
    AdminUserStatsDTO, GeographicDistributionDTO,
    AdminUserListRequestDTO, derive_clv_status,
)
from tuned.core.exceptions import DatabaseError
from tuned.core.logging import get_logger

logger = get_logger(__name__)


class GetAdminUserList:
    """Fetches paginated list of clients with aggregated business metrics."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, req: AdminUserListRequestDTO) -> AdminUserListResponseDTO:
        try:
            from tuned.models.payment import Payment

            # Subquery: total_spent per user from completed payments
            spent_sub = (
                select(
                    Payment.user_id.label("user_id"),
                    func.coalesce(func.sum(Payment.amount), 0).label("total_spent"),
                )
                .where(Payment.status == PaymentStatus.COMPLETED)
                .group_by(Payment.user_id)
                .subquery()
            )

            # Subquery: orders_count and last_order_at per user
            orders_sub = (
                select(
                    Order.client_id.label("user_id"),
                    func.count(Order.id).label("orders_count"),
                    func.max(Order.created_at).label("last_order_at"),
                )
                .group_by(Order.client_id)
                .subquery()
            )

            # Base query: non-admin users with joined aggregates
            stmt = (
                select(
                    User,
                    func.coalesce(spent_sub.c.total_spent, 0).label("total_spent"),
                    func.coalesce(orders_sub.c.orders_count, 0).label("orders_count"),
                    orders_sub.c.last_order_at.label("last_order_at"),
                )
                .outerjoin(spent_sub, spent_sub.c.user_id == User.id)
                .outerjoin(orders_sub, orders_sub.c.user_id == User.id)
                .where(User.is_admin == False)
            )

            # Search filter
            if req.q:
                pattern = f"%{req.q}%"
                stmt = stmt.where(
                    or_(
                        User.username.ilike(pattern),
                        User.email.ilike(pattern),
                    )
                )

            # CLV status filter
            if req.clv_status:
                col = func.coalesce(spent_sub.c.total_spent, 0)
                if req.clv_status == "high":
                    stmt = stmt.where(col >= 500)
                elif req.clv_status == "medium":
                    stmt = stmt.where(and_(col >= 100, col < 500))
                elif req.clv_status == "low":
                    stmt = stmt.where(and_(col > 0, col < 100))
                elif req.clv_status == "normal":
                    stmt = stmt.where(col == 0)

            # Status filter
            if req.status:
                thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
                col = orders_sub.c.last_order_at
                if req.status == "active":
                    stmt = stmt.where(col >= thirty_days_ago)
                elif req.status == "dormant":
                    stmt = stmt.where(or_(col.is_(None), col < thirty_days_ago))

            # Sorting
            sort_map = {
                "created_at": User.created_at,
                "total_spent": spent_sub.c.total_spent,
                "orders_count": orders_sub.c.orders_count,
                "name": User.username,
                "last_order_at": orders_sub.c.last_order_at,
            }
            sort_col = sort_map.get(req.sort or "created_at", User.created_at)
            order_fn = desc if (req.order or "desc") == "desc" else asc
            stmt = stmt.order_by(order_fn(sort_col))

            # Count total
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = self.session.scalar(count_stmt) or 0

            # Pagination
            page = max(req.page or 1, 1)
            per_page = min(req.per_page or 5, 50)
            stmt = stmt.offset((page - 1) * per_page).limit(per_page)

            rows = self.session.execute(stmt).all()

            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

            users: list[AdminUserInsightDTO] = []
            for user, total_spent, orders_count, last_order_at in rows:
                total_spent_float = float(total_spent or 0)
                clv = derive_clv_status(total_spent_float)
                last_order_str: Optional[str] = None
                user_status = "dormant"
                if last_order_at:
                    last_order_str = last_order_at.isoformat()
                    # Make last_order_at timezone aware for comparison
                    last_tz = last_order_at.replace(tzinfo=timezone.utc) if last_order_at.tzinfo is None else last_order_at
                    if last_tz >= thirty_days_ago:
                        user_status = "active"

                users.append(AdminUserInsightDTO(
                    id=str(user.id),
                    name=user.username,
                    email=user.email,
                    avatar_url=user.get_profile_pic_url() if user.profile_pic_id else None,
                    orders_count=int(orders_count or 0),
                    total_spent=f"{total_spent_float:.2f}",
                    clv_status=clv,
                    last_order_at=last_order_str,
                    status=user_status,
                ))

            return AdminUserListResponseDTO(
                users=users,
                total=total,
                page=page,
                per_page=per_page,
            )
        except Exception as exc:
            logger.error("[GetAdminUserList] %s", exc)
            raise DatabaseError(str(exc)) from exc


class GetAdminUserStats:
    """Aggregates global user KPI statistics."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self) -> AdminUserStatsDTO:
        try:
            from tuned.models.payment import Payment
            now = datetime.now(timezone.utc)
            this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)

            total_clients = self.session.scalar(
                select(func.count(User.id)).where(User.is_admin == False)
            ) or 0

            clients_this_month = self.session.scalar(
                select(func.count(User.id))
                .where(User.is_admin == False, User.created_at >= this_month_start)
            ) or 0

            clients_last_month = self.session.scalar(
                select(func.count(User.id))
                .where(
                    User.is_admin == False,
                    User.created_at >= last_month_start,
                    User.created_at < this_month_start,
                )
            ) or 0

            # Returning clients: placed more than 1 order
            returning_sub = (
                select(Order.client_id)
                .join(User, User.id == Order.client_id)
                .where(User.is_admin == False)
                .group_by(Order.client_id)
                .having(func.count(Order.id) > 1)
                .subquery()
            )
            returning = self.session.scalar(
                select(func.count()).select_from(returning_sub)
            ) or 0
            returning_pct = (returning / total_clients * 100) if total_clients > 0 else 0.0

            # Dormant: no order in last 30 days
            thirty_days_ago = now - timedelta(days=30)
            active_client_ids = select(func.distinct(Order.client_id)).where(
                Order.created_at >= thirty_days_ago
            )
            dormant_count = self.session.scalar(
                select(func.count(User.id))
                .where(User.is_admin == False, User.id.not_in(active_client_ids))
            ) or 0

            # High value: total_spent >= 500
            high_value_sub = (
                select(Payment.user_id)
                .join(User, User.id == Payment.user_id)
                .where(User.is_admin == False, Payment.status == PaymentStatus.COMPLETED)
                .group_by(Payment.user_id)
                .having(func.sum(Payment.amount) >= 500)
                .subquery()
            )
            high_value = self.session.scalar(
                select(func.count()).select_from(high_value_sub)
            ) or 0

            # Retention rate = returning_clients / total_clients
            retention_rate = (returning / total_clients * 100) if total_clients > 0 else 0.0

            return AdminUserStatsDTO(
                total_clients=total_clients,
                total_clients_growth_this_month=clients_this_month,
                returning_clients_percentage=round(returning_pct, 1),
                returning_clients_growth_vs_last_month=clients_last_month,
                dormant_clients_count=dormant_count,
                high_value_clients_count=high_value,
                client_retention_rate=round(retention_rate, 1),
            )
        except Exception as exc:
            logger.error("[GetAdminUserStats] %s", exc)
            raise DatabaseError(str(exc)) from exc


class GetGeographicDistribution:
    """Returns client distribution by country from user localization settings."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self) -> list[GeographicDistributionDTO]:
        try:
            from tuned.models.preferences import UserLocalizationSettings as ULS

            # Get geographic counts with default "US" fallback for users without localization preferences record
            rows = self.session.execute(
                select(
                    func.coalesce(ULS.country_code, "US").label("cc"),
                    func.count(User.id).label("cnt")
                )
                .select_from(User)
                .outerjoin(ULS, User.id == ULS.user_id)
                .where(User.is_admin == False)
                .group_by(func.coalesce(ULS.country_code, "US"))
                .order_by(desc("cnt"))
            ).all()

            total = sum(r.cnt for r in rows)
            if total == 0:
                return []

            COUNTRY_NAMES: dict[str, str] = {
                "US": "United States", "GB": "United Kingdom",
                "KE": "Kenya", "NG": "Nigeria", "AU": "Australia",
                "CA": "Canada", "IN": "India", "ZA": "South Africa",
            }

            results: list[GeographicDistributionDTO] = []
            other_count = 0
            for row in rows:
                cc = (row.cc or "").upper()
                if not cc or cc not in COUNTRY_NAMES:
                    other_count += row.cnt
                    continue
                results.append(GeographicDistributionDTO(
                    country_code=cc,
                    country_name=COUNTRY_NAMES.get(cc, cc),
                    percentage=round(row.cnt / total * 100, 1),
                ))

            if other_count > 0:
                results.append(GeographicDistributionDTO(
                    country_code="OT",
                    country_name="Other",
                    percentage=round(other_count / total * 100, 1),
                ))

            return results
        except Exception as exc:
            logger.error("[GetGeographicDistribution] %s", exc)
            raise DatabaseError(str(exc)) from exc
