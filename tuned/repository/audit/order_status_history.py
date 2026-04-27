from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from tuned.models import OrderStatusHistory
from tuned.dtos import OrderStatusHistoryCreateDTO, OrderStatusHistoryResponseDTO
from tuned.repository.exceptions import DatabaseError, NotFound

class CreateOrderStatusHistory:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, data: OrderStatusHistoryCreateDTO) -> OrderStatusHistoryResponseDTO:
        try:
            history = OrderStatusHistory(
                order_id=data.order_id,
                user_id=data.user_id,
                old_status=data.old_status,
                new_status=data.new_status,
                notes=data.notes,
                ip_address=data.ip_address
            )
            self.session.add(history)
            self.session.flush()
            return OrderStatusHistoryResponseDTO.from_model(history)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while creating order status history: {str(e)}") from e

class GetOrderStatusHistoryByID:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, history_id: str) -> OrderStatusHistoryResponseDTO:
        try:
            stmt = select(OrderStatusHistory).where(OrderStatusHistory.id == history_id)
            history = self.session.scalar(stmt)
            if not history:
                raise NotFound("Order status history record not found.")
            return OrderStatusHistoryResponseDTO.from_model(history)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching status history: {str(e)}") from e

class GetOrderStatusHistoryByOrder:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, order_id: str, page: int = 1, per_page: int = 20) -> tuple[list[OrderStatusHistoryResponseDTO], int]:
        try:
            stmt = select(OrderStatusHistory).where(OrderStatusHistory.order_id == order_id)
            
            # Count total
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = self.session.scalar(count_stmt) or 0
            
            stmt = stmt.order_by(OrderStatusHistory.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
            items = self.session.scalars(stmt).all()
            
            return [OrderStatusHistoryResponseDTO.from_model(i) for i in items], total
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching history for order: {str(e)}") from e

class OrderStatusHistoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: OrderStatusHistoryCreateDTO) -> OrderStatusHistoryResponseDTO:
        return CreateOrderStatusHistory(self.session).execute(data)

    def get_by_id(self, history_id: str) -> OrderStatusHistoryResponseDTO:
        return GetOrderStatusHistoryByID(self.session).execute(history_id)

    def get_by_order(self, order_id: str, page: int = 1, per_page: int = 20) -> tuple[list[OrderStatusHistoryResponseDTO], int]:
        return GetOrderStatusHistoryByOrder(self.session).execute(order_id, page, per_page)
