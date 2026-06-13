from __future__ import annotations
from typing import TYPE_CHECKING
from tuned.core.logging import get_logger
from tuned.dtos.order import OrderListRequestDTO
from tuned.dtos.admin.orders import (
    AdminOrderListResponseDTO, AdminOrdersStatsResponseDTO,
)


if TYPE_CHECKING:
    from tuned.repository import Repository

logger = get_logger(__name__)


class AdminOrderService:
    def __init__(self, repos: "Repository") -> None:
        self._repos = repos

    def list_all_orders(self, req: OrderListRequestDTO) -> AdminOrderListResponseDTO:
        result = self._repos.admin_orders.get_all_orders(req)
        self._repos.session.commit()
        return result

    def get_orders_stats(self) -> AdminOrdersStatsResponseDTO:
        result = self._repos.admin_orders.get_admin_order_stats()
        return result

    def activate_order(self, order_id: str) -> dict:
        order = self._repos.admin_orders.activate_order(order_id)
        self._repos.session.commit()
        # Emit events
        try:
            from tuned.core.events import get_event_bus
            get_event_bus().emit("order.status_changed", {
                "order_id": str(order.id),
                "client_id": str(order.client_id),
                "new_status": order.status.value,
                "old_status": "pending",
                "order_number": order.order_number,
                "progress": 40,
                "delivered_at": None,
            })
            get_event_bus().emit("admin.order.activated", {
                "order_id": str(order.id),
                "order_number": order.order_number,
            })
        except Exception as exc:
            logger.error("[AdminOrderService.activate_order] Event emit failed: %r", exc)
        return {"success": True, "message": f"Order {order.order_number} activated"}

    def escalate_order(self, order_id: str) -> dict:
        order = self._repos.admin_orders.escalate_order(order_id)
        self._repos.session.commit()
        try:
            from tuned.core.events import get_event_bus
            get_event_bus().emit("admin.order.escalated", {
                "order_id": str(order.id),
                "order_number": order.order_number,
            })
        except Exception as exc:
            logger.error("[AdminOrderService.escalate_order] Event emit failed: %r", exc)
        return {"success": True, "message": f"Order {order.order_number} escalated"}
