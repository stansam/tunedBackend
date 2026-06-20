from typing import Sequence
from tuned.dtos.order_delivery import(
    CreateOrderDeliveryDTO,
    UpdateOrderDeliveryStatusDTO, AddDeliveryFilesDTO
)
from tuned.models.order_delivery import OrderDelivery
from tuned.repository.order_delivery.delivery import(
    CreateOrderDelivery,
    GetOrderDeliveries,
    GetOrderDeliveryByID,
    UpdateDeliveryStatus,
    MarkDeliveryClientNotified,
    DeleteOrderDelivery
)
from tuned.repository.order_delivery.files import AddFilesToDelivery
from tuned.repository.protocols import OrderDeliveryRepositoryProtocol
from tuned.core.exceptions import DatabaseError
from sqlalchemy.exc import SQLAlchemyError

class OrderDeliveryRepository(OrderDeliveryRepositoryProtocol):
    def __init__(self, session) -> None:
        self.session = session

    def create_order_delivery(self, data: CreateOrderDeliveryDTO) -> OrderDelivery:
        return CreateOrderDelivery(self.session).execute(data)
    
    def get_by_id(self, delivery_id: str) -> OrderDelivery:
        return GetOrderDeliveryByID(self.session).execute(delivery_id)
    
    def get_order_deliveries(self, order_id: str) -> Sequence[OrderDelivery]:
        return GetOrderDeliveries(self.session).execute(order_id)
    
    def update_status(self, delivery_id: str, data: UpdateOrderDeliveryStatusDTO) -> OrderDelivery:
        return UpdateDeliveryStatus(self.session).execute(delivery_id, data)
    
    def add_files(self, delivery_id: str, data: AddDeliveryFilesDTO) -> OrderDelivery:
        return AddFilesToDelivery(self.session).execute(delivery_id, data)
    
    def mark_client_notified(self, delivery_id: str) -> OrderDelivery:
        return MarkDeliveryClientNotified(self.session).execute(delivery_id)
    
    def delete(self, delivery_id: str, user_id: str) -> None:
        return DeleteOrderDelivery(self.session).execute(delivery_id, user_id)
    def save(self) -> None:
        try:
            self.session.commit()
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseError(f"Database error while saving order changes: {exc}") from exc

    def rollback(self) -> None:
        self.session.rollback()
