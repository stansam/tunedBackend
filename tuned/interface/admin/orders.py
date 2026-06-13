from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from tuned.core.logging import get_logger
from tuned.dtos.order import OrderListRequestDTO
from tuned.dtos.admin import (
    AdminOrderListResponseDTO, AdminOrdersStatsResponseDTO,
    AdminOrderDetailResponseDTO, AdminRevisionRequestResponseDTO,
    AdminDeadlineExtensionResponseDTO,
)
from tuned.models.enums import RevisionRequestStatus, Priority

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

    def get_order_detail(self, order_number: str) -> AdminOrderDetailResponseDTO:
        order = self._repos.order.get_order_by_order_number(order_number)
        return AdminOrderDetailResponseDTO.from_model(order)

    def get_revision_requests(self, order_id: str) -> list[AdminRevisionRequestResponseDTO]:
        requests = self._repos.admin_orders.get_revision_requests(order_id)
        return [AdminRevisionRequestResponseDTO.from_model(r) for r in requests]

    def update_revision_request_status(
        self, order_id: str, request_id: str, reviewed_by: str,
        new_status: RevisionRequestStatus, internal_notes: Optional[str] = None
    ) -> AdminRevisionRequestResponseDTO:
        from tuned.core.exceptions import NotFound
        req = self._repos.admin_orders.update_revision_status(
            request_id, reviewed_by, new_status, internal_notes
        )
        if str(req.order_id) != order_id:
            raise NotFound("Revision request not found for this order")
        self._repos.session.commit()
        return AdminRevisionRequestResponseDTO.from_model(req)

    def get_deadline_extensions(self, order_id: str) -> list[AdminDeadlineExtensionResponseDTO]:
        reqs = self._repos.admin_orders.get_deadline_extensions(order_id)
        return [AdminDeadlineExtensionResponseDTO.from_model(r) for r in reqs]

    def create_deadline_extension(
        self, order_id: str, requested_by: str,
        requested_hours: int, reason: str, priority: Priority
    ) -> AdminDeadlineExtensionResponseDTO:
        ext_req = self._repos.admin_orders.create_deadline_extension(
            order_id, requested_by, requested_hours, reason, priority
        )
        self._repos.session.commit()
        try:
            order = self._repos.order.get_by_id(order_id)
            from tuned.core.events import get_event_bus
            get_event_bus().emit("order.deadline_extension_requested", {
                "client_id": str(order.client_id),
                "order_id": order_id,
                "order_number": order.order_number,
                "requested_hours": requested_hours,
            })
        except Exception as exc:
            logger.error("[AdminOrderService.create_deadline_extension] Event failed: %r", exc)
        return AdminDeadlineExtensionResponseDTO.from_model(ext_req)
