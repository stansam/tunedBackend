from __future__ import annotations
import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, select, and_
from sqlalchemy.exc import SQLAlchemyError
from tuned.models import Order, Service
from tuned.models.enums import OrderStatus
from tuned.dtos.order import OrderListRequestDTO
from tuned.repository.order.orders import getOrderListResponse
from tuned.dtos.admin.orders import (
    AdminOrderResponseDTO, AdminOrderListResponseDTO,
    AdminOrdersStatsDTO, AdminBottleneckStatsDTO,
    AdminServiceLoadDTO, AdminOrdersStatsResponseDTO,
)
from tuned.core.exceptions import DatabaseError, NotFound
from tuned.core.logging import get_logger

logger = get_logger(__name__)

_ACTIVE = (OrderStatus.PENDING, OrderStatus.ACTIVE, OrderStatus.REVISION)


class GetAllOrders:
    """Lists all orders across all clients with optional filters."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, req: OrderListRequestDTO) -> AdminOrderListResponseDTO:
        try:
            # Base statement: no client_id filter (admin sees all)
            stmt = select(Order)
            # Reuse the shared filter/sort/paginate helper from the client repository
            list_response = getOrderListResponse(self.session, stmt, req)
            
            # Fetch complete model instances with joins
            order_ids = [uuid_id for o in list_response.orders if (uuid_id := o.id)]
            
            orders_map = {}
            if order_ids:
                stmt_full = select(Order).where(Order.id.in_(order_ids))
                full_orders = self.session.scalars(stmt_full).all()
                orders_map = {str(o.id): o for o in full_orders}
                
            admin_orders = []
            for o in list_response.orders:
                full_o = orders_map.get(o.id)
                if full_o:
                    admin_orders.append(AdminOrderResponseDTO.from_model(full_o))
                
            return AdminOrderListResponseDTO(
                orders=admin_orders,
                total=list_response.total,
                page=list_response.page,
                per_page=list_response.per_page,
                sort=list_response.sort,
                order=list_response.order,
            )
        except SQLAlchemyError as exc:
            logger.error("[GetAllOrders] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc
        except Exception as exc:
            logger.error("[GetAllOrders] Unexpected error: %s", exc)
            raise DatabaseError(str(exc)) from exc


class GetAdminOrdersStats:
    """Computes status counts, bottleneck breakdown, and service load."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self) -> AdminOrdersStatsResponseDTO:
        try:
            def count_status(status: OrderStatus) -> int:
                return self.session.scalar(
                    select(func.count(Order.id)).where(Order.status == status)
                ) or 0

            all_count = self.session.scalar(select(func.count(Order.id))) or 0
            pending   = count_status(OrderStatus.PENDING)
            active    = count_status(OrderStatus.ACTIVE)
            revision  = count_status(OrderStatus.REVISION)
            completed = count_status(OrderStatus.COMPLETED)
            overdue   = count_status(OrderStatus.OVERDUE)

            stats = AdminOrdersStatsDTO(
                all=all_count,
                pending=pending,
                in_progress=active + revision,
                revision=revision,
                completed=completed,
                overdue=overdue,
            )

            # Bottlenecks
            pending_activation = pending
            under_review = count_status(OrderStatus.COMPLETED_PENDING_REVIEW)
            awaiting_payment = self.session.scalar(
                select(func.count(Order.id))
                .where(Order.paid == False, Order.status != OrderStatus.DRAFT)
            ) or 0

            bottlenecks = AdminBottleneckStatsDTO(
                pending_activation=pending_activation,
                under_review=under_review,
                awaiting_payment=awaiting_payment,
            )

            # Service load: count active/revision/pending orders per service
            service_rows = self.session.execute(
                select(Service, func.count(Order.id).label("order_count"))
                .join(Order, Order.service_id == Service.id)
                .where(
                    Order.status.in_(_ACTIVE)
                )
                .group_by(Service.id)
                .order_by(func.count(Order.id).desc())
                .limit(10)
            ).all()

            service_load = []
            for service, count in service_rows:
                if count >= 8:
                    status = "Busy"
                elif count >= 3:
                    status = "OK"
                else:
                    status = "Free"
                service_load.append(AdminServiceLoadDTO(
                    id=str(service.id),
                    name=service.name,
                    orders_count=count,
                    status=status,
                ))

            return AdminOrdersStatsResponseDTO(
                stats=stats,
                bottlenecks=bottlenecks,
                service_load=service_load,
            )
        except SQLAlchemyError as exc:
            logger.error("[GetAdminOrdersStats] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc
        except Exception as exc:
            logger.error("[GetAdminOrdersStats] Unexpected error: %s", exc)
            raise DatabaseError(str(exc)) from exc


class ActivateOrder:
    """Transitions order status from PENDING to ACTIVE."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, order_id: str) -> Order:
        try:
            order = self.session.scalar(select(Order).where(Order.id == order_id))
            if not order:
                raise NotFound(f"Order {order_id} not found")
            if order.status != OrderStatus.PENDING:
                raise ValueError(f"Order status must be pending to activate (current: {order.status.value})")
            
            order.status = OrderStatus.ACTIVE
            self.session.flush()
            return order
        except (NotFound, ValueError):
            raise
        except SQLAlchemyError as exc:
            logger.error("[ActivateOrder] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc
        except Exception as exc:
            logger.error("[ActivateOrder] Unexpected error: %s", exc)
            raise DatabaseError(str(exc)) from exc


class EscalateOrder:
    """Sets escalated=True on an overdue order."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, order_id: str) -> Order:
        try:
            order = self.session.scalar(select(Order).where(Order.id == order_id))
            if not order:
                raise NotFound(f"Order {order_id} not found")
            order.escalated = True
            self.session.flush()
            return order
        except NotFound:
            raise
        except SQLAlchemyError as exc:
            logger.error("[EscalateOrder] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc
        except Exception as exc:
            logger.error("[EscalateOrder] Unexpected error: %s", exc)
            raise DatabaseError(str(exc)) from exc
