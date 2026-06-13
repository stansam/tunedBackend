from __future__ import annotations

from typing import Optional
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from tuned.models import(
    Order, OrderFile, OrderComment,
    Discount, OrderStatus
)
from tuned.dtos import(
    OrderListRequestDTO, OrderListResponseDTO,
    CreateOrderRequestDTO, OrderDraftCreateDTO, CreateOrderFileDTO,
)
from tuned.repository.order.files import (
    CreateOrderFile, GetOrderFileById
)
from tuned.repository.order.orders import(
    GetActiveOrdersByClient,
    GetOrderById,
    GetLatestActiveOrderByClient,
    GetUpcomingDeadlines,
    GetProjectLifecycle,
    GetOrderByClient,
    GetOrderForReorder,
    GetClientOrders,
    CreateOrder,
    GetOrderForClientByOrderNumber,
    GetOrderByOrderNumber,
    CreateOrderFromReorder,
    UpdateOrderStatus,
)
from tuned.repository.order.discount import LinkDiscountToOrder, GetDiscountByCode
from tuned.repository.order.drafts import UpsertDraftOrder, GetDraftOrder
from tuned.core.exceptions import DatabaseError
from tuned.repository.protocols import OrderRepositoryProtocol
from tuned.repository.order.comments import (
    GetOrderComments, CreateOrderComment, UpdateOrderComment,
    DeleteOrderComment, LinkFilesToComment, MarkCommentsRead,
)


class OrderRepository(OrderRepositoryProtocol):
    def __init__(self, session: Session) -> None:
        self.session = session

    def _get_order_by_id_for_client(self, order_id: str, client_id: str) -> Order:
        return GetOrderByClient(self.session).execute(order_id, client_id)
    def get_by_id(self, order_id: str) -> Order:
        return GetOrderById(self.session).execute(order_id)
        
    def get_active_orders(self, client_id: str) -> list[Order]:
        return GetActiveOrdersByClient(self.session).execute(client_id)

    def get_paid_order_count(self, client_id: str) -> int:
        stmt = (
            select(func.count(Order.id))
            .where(Order.client_id == client_id, Order.paid == True)
        )
        return self.session.scalar(stmt) or 0

    def get_latest_active_order(self, client_id: str) -> Optional[Order]:
        return GetLatestActiveOrderByClient(self.session).execute(client_id)

    def get_upcoming_deadlines(self, client_id: str, limit: int = 3) -> list[Order]:
        return GetUpcomingDeadlines(self.session).execute(client_id, limit)

    def get_project_lifecycle(self, client_id: str) -> list[tuple[str, int]]:
        return GetProjectLifecycle(self.session).execute(client_id)

    def get_order_by_order_number_for_client(self, order_number: str, client_id: str) -> Order:
        return GetOrderForClientByOrderNumber(self.session).execute(order_number, client_id)

    def get_order_by_order_number(self, order_number: str) -> Order:
        return GetOrderByOrderNumber(self.session).execute(order_number)
    
    def get_order_by_id_for_client(self, order_id: str, client_id: str) -> Order:
        return self._get_order_by_id_for_client(order_id, client_id)

    def get_order_for_reorder(self, order_id: str, client_id: str) -> Order:
        return GetOrderForReorder(self.session).execute(order_id, client_id)

    def list_client_orders(self, client_id: str, req: OrderListRequestDTO) -> OrderListResponseDTO:
        return GetClientOrders(self.session).execute(client_id, req)

    def apply_discount(self, order_id: str, client_id: str, discount_amount: float) -> Order:
        order = self._get_order_by_id_for_client(order_id, client_id)
        order.discount_amount = (order.discount_amount or Decimal('0.0')) + Decimal(str(discount_amount))
        order.total_price = max((order.subtotal or Decimal('0.0')) - (order.discount_amount or Decimal('0.0')), Decimal('0.0'))
        self.session.flush()
        return order

    def create_reorder(self, source: Order, client_id: str) -> Order:
        return CreateOrderFromReorder(self.session).execute(source, client_id)

    def create_order(self, client_id: str, dto: CreateOrderRequestDTO, total_price: float, subtotal: float) -> Order:
        return CreateOrder(self.session).execute(client_id, dto, total_price, subtotal)

    def update_order_status(self, order_id: str, status: OrderStatus) -> Order:
        return UpdateOrderStatus(self.session).execute(order_id, status)

    def get_discount_by_code(self, code: str) -> Optional[Discount]:
        return GetDiscountByCode(self.session).execute(code)

    def link_discount_to_order(self, order: Order, discount: Discount, amount: float) -> None:
        return LinkDiscountToOrder(self.session).execute(order, discount, amount)

    def create_order_file(self, order_id: str, req: CreateOrderFileDTO) -> OrderFile:
        return CreateOrderFile(self.session).execute(order_id, req)

    def get_order_file_by_id(self, file_id: str, order_id: str) -> OrderFile:
        return GetOrderFileById(self.session).execute(file_id, order_id)

    def upsert_draft(self, dto: OrderDraftCreateDTO) -> Order:
        return UpsertDraftOrder(self.session).execute(dto)

    def get_draft(self, user_id: str) -> Optional[Order]:
        return GetDraftOrder(self.session).execute(user_id)

    def get_order_comments(self, order_id: str) -> list[OrderComment]:
        return GetOrderComments(self.session).execute(order_id)

    def create_order_comment(self, order_id: str, user_id: str, content: str) -> OrderComment:
        return CreateOrderComment(self.session).execute(order_id, user_id, content)

    def update_order_comment(self, comment_id: str, user_id: str, content: str) -> OrderComment:
        return UpdateOrderComment(self.session).execute(comment_id, user_id, content)

    def delete_order_comment(self, comment_id: str, user_id: str) -> None:
        return DeleteOrderComment(self.session).execute(comment_id, user_id)

    def link_files_to_comment(self, comment_id: str, file_ids: list[str]) -> None:
        return LinkFilesToComment(self.session).execute(comment_id, file_ids)

    def mark_comments_read(self, order_id: str, reader_user_id: str) -> None:
        return MarkCommentsRead(self.session).execute(order_id, reader_user_id)

    def get_active_orders_count(self) -> int:
        _NAV_ACTIVE_STATUSES = (
            OrderStatus.PENDING,
            OrderStatus.ACTIVE,
            OrderStatus.REVISION,
        )
        stmt = select(func.count(Order.id)).where(
            Order.status.in_(_NAV_ACTIVE_STATUSES)
        )
        return self.session.scalar(stmt) or 0

    def get_unpaid_completed_orders_count(self) -> int:
        stmt = select(func.count(Order.id)).where(
            Order.status == OrderStatus.COMPLETED_PENDING_REVIEW,
            Order.paid == False
        )
        return self.session.scalar(stmt) or 0

    def get_unread_comments_count(self) -> int:
        stmt = select(func.count(OrderComment.id)).where(
            OrderComment.is_admin == False,
            OrderComment.is_read == False,
        )
        return self.session.scalar(stmt) or 0

    def save(self) -> None:
        try:
            self.session.commit()
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseError(f"Database error while saving order changes: {exc}") from exc

    def rollback(self) -> None:
        self.session.rollback()
