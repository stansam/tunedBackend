from __future__ import annotations

import logging
from typing import Any, Dict, TYPE_CHECKING
from tuned.core.logging import get_logger

if TYPE_CHECKING:
    from tuned.core.events import EventBus

logger: logging.Logger = get_logger(__name__)


class ContentEventHandlers:
    def __init__(self, bus: EventBus) -> None:
        self._bus = bus

    def register(self) -> None:
        self._bus.on("service_category.created", self._on_category_created)
        self._bus.on("service_category.updated", self._on_category_updated)
        self._bus.on("service_category.deleted", self._on_category_deleted)
        self._bus.on("service.created", self._on_service_created)
        self._bus.on("service.updated", self._on_service_updated)
        self._bus.on("service.deleted", self._on_service_deleted)
        self._bus.on("sample.created", self._on_sample_created)
        self._bus.on("sample.updated", self._on_sample_updated)
        self._bus.on("sample.deleted", self._on_sample_deleted)
        self._bus.on("testimonial.created", self._on_testimonial_created)
        self._bus.on("testimonial.updated", self._on_testimonial_updated)
        self._bus.on("testimonial.deleted", self._on_testimonial_deleted)
        logger.info("[ContentEventHandlers] registered")

    def _on_category_created(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info("[ContentEventHandlers] Processing service_category.created: %s", event_data.get("id"))
            from tuned.extensions import socketio
            socketio.emit("admin:category:created", event_data, to="admin_room")
        except Exception as exc:
            logger.error("[ContentEventHandlers] Error in service_category.created handler: %r", exc)

    def _on_category_updated(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info("[ContentEventHandlers] Processing service_category.updated: %s", event_data.get("id"))
            from tuned.extensions import socketio
            socketio.emit("admin:category:updated", event_data, to="admin_room")
        except Exception as exc:
            logger.error("[ContentEventHandlers] Error in service_category.updated handler: %r", exc)

    def _on_category_deleted(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info("[ContentEventHandlers] Processing service_category.deleted: %s", event_data.get("id"))
            from tuned.extensions import socketio
            socketio.emit("admin:category:deleted", event_data, to="admin_room")
        except Exception as exc:
            logger.error("[ContentEventHandlers] Error in service_category.deleted handler: %r", exc)

    def _on_service_created(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info("[ContentEventHandlers] Processing service.created: %s", event_data.get("id"))
            from tuned.extensions import socketio
            socketio.emit("admin:service:created", event_data, to="admin_room")
        except Exception as exc:
            logger.error("[ContentEventHandlers] Error in service.created handler: %r", exc)

    def _on_service_updated(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info("[ContentEventHandlers] Processing service.updated: %s", event_data.get("id"))
            from tuned.extensions import socketio
            socketio.emit("admin:service:updated", event_data, to="admin_room")
        except Exception as exc:
            logger.error("[ContentEventHandlers] Error in service.updated handler: %r", exc)

    def _on_service_deleted(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info("[ContentEventHandlers] Processing service.deleted: %s", event_data.get("id"))
            from tuned.extensions import socketio
            socketio.emit("admin:service:deleted", event_data, to="admin_room")
        except Exception as exc:
            logger.error("[ContentEventHandlers] Error in service.deleted handler: %r", exc)

    def _on_sample_created(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info("[ContentEventHandlers] Processing sample.created: %s", event_data.get("id"))
            from tuned.extensions import socketio
            socketio.emit("admin:sample:created", event_data, to="admin_room")
        except Exception as exc:
            logger.error("[ContentEventHandlers] Error in sample.created handler: %r", exc)

    def _on_sample_updated(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info("[ContentEventHandlers] Processing sample.updated: %s", event_data.get("id"))
            from tuned.extensions import socketio
            socketio.emit("admin:sample:updated", event_data, to="admin_room")
        except Exception as exc:
            logger.error("[ContentEventHandlers] Error in sample.updated handler: %r", exc)

    def _on_sample_deleted(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info("[ContentEventHandlers] Processing sample.deleted: %s", event_data.get("id"))
            from tuned.extensions import socketio
            socketio.emit("admin:sample:deleted", event_data, to="admin_room")
        except Exception as exc:
            logger.error("[ContentEventHandlers] Error in sample.deleted handler: %r", exc)

    def _on_testimonial_created(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info("[ContentEventHandlers] Processing testimonial.created: %s", event_data.get("id"))
            from tuned.extensions import socketio
            socketio.emit("admin:testimonial:created", event_data, to="admin_room")
        except Exception as exc:
            logger.error("[ContentEventHandlers] Error in testimonial.created handler: %r", exc)

    def _on_testimonial_updated(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info("[ContentEventHandlers] Processing testimonial.updated: %s", event_data.get("id"))
            from tuned.extensions import socketio
            socketio.emit("admin:testimonial:updated", event_data, to="admin_room")
        except Exception as exc:
            logger.error("[ContentEventHandlers] Error in testimonial.updated handler: %r", exc)

    def _on_testimonial_deleted(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info("[ContentEventHandlers] Processing testimonial.deleted: %s", event_data.get("id"))
            from tuned.extensions import socketio
            socketio.emit("admin:testimonial:deleted", event_data, to="admin_room")
        except Exception as exc:
            logger.error("[ContentEventHandlers] Error in testimonial.deleted handler: %r", exc)
