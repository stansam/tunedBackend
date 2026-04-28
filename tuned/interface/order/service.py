from __future__ import annotations

import logging
from typing import Optional
from tuned.core.logging import get_logger
from tuned.dtos.audit import ActivityLogCreateDTO
from tuned.dtos.order import ReorderResponseDTO
from tuned.interface.audit import audit_service
from tuned.repository import repositories
from tuned.repository.exceptions import DatabaseError, NotFound
from tuned.repository.protocols import OrderRepositoryProtocol
from tuned.interface.audit.activity_log import ActivityLogService

logger: logging.Logger = get_logger(__name__)


class OrderService:
    def __init__(
        self,
        repo: Optional[OrderRepositoryProtocol] = None,
        audit_service_dependency: Optional[ActivityLogService] = None,
    ) -> None:
        self._repo = repo or repositories.order
        self._audit = audit_service_dependency or audit_service.activity_log

    def reorder(self, order_id: str, user_id: str) -> ReorderResponseDTO:
        try:
            source = self._repo.get_order_for_reorder(order_id, user_id)
            new_order = self._repo.create_reorder(source, user_id)

            try:
                self._audit.log(ActivityLogCreateDTO(
                    action="order_reordered",
                    user_id=user_id,
                    entity_type="Order",
                    entity_id=str(new_order.id),
                    after={"source_order_id": order_id},
                    created_by=user_id,
                ))
            except Exception as audit_exc:
                logger.error(
                    "[OrderService.reorder] Audit failed for new order %s: %r",
                    new_order.id, audit_exc,
                )

            try:
                from tuned.core.events import get_event_bus
                get_event_bus().emit("order.created", {
                    "order_id":     str(new_order.id),
                    "client_id":    user_id,
                    "order_number": new_order.order_number,
                })
            except Exception as event_exc:
                logger.error(
                    "[OrderService.reorder] Event emit failed for %s: %r",
                    new_order.id, event_exc,
                )

            self._repo.save()
            logger.info(
                "[OrderService.reorder] User %s reordered %s → new order %s",
                user_id, order_id, new_order.order_number,
            )
            return ReorderResponseDTO(
                order_id=str(new_order.id),
                order_number=new_order.order_number,
                redirect_url=f"/client/orders/{new_order.id}",
            )

        except NotFound:
            self._repo.rollback()
            logger.warning(
                "[OrderService.reorder] Order %s not found for user %s",
                order_id, user_id,
            )
            raise
        except DatabaseError:
            self._repo.rollback()
            logger.error(
                "[OrderService.reorder] DB error for order %s user %s",
                order_id, user_id,
            )
            raise
        except Exception:
            self._repo.rollback()
            raise
