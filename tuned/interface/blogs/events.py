from __future__ import annotations

import logging
from typing import Any, Dict, TYPE_CHECKING
from tuned.core.logging import get_logger

if TYPE_CHECKING:
    from tuned.core.events import EventBus

logger: logging.Logger = get_logger(__name__)


class BlogEventHandlers:

    def __init__(self, bus: "EventBus") -> None:
        self._bus = bus

    def register(self) -> None:
        self._bus.on("blog.post.created", self._on_post_created)
        self._bus.on("blog.post.updated", self._on_post_updated)
        self._bus.on("blog.post.deleted", self._on_post_deleted)
        self._bus.on("blog.post.published", self._on_post_published)
        self._bus.on("blog.category.created", self._on_category_created)
        self._bus.on("blog.category.updated", self._on_category_updated)
        self._bus.on("blog.category.deleted", self._on_category_deleted)
        self._bus.on("blog.comment.updated", self._on_comment_updated)
        logger.info("[BlogEventHandlers] registered")

    def _on_post_created(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info("[BlogEventHandlers] blog.post.created: %s", event_data.get("id"))
            from tuned.extensions import socketio
            socketio.emit("admin:blog:post:created", event_data, to="admin_room")
        except Exception as exc:
            logger.error("[BlogEventHandlers] Error in blog.post.created handler: %r", exc)

    def _on_post_updated(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info("[BlogEventHandlers] blog.post.updated: %s", event_data.get("id"))
            from tuned.extensions import socketio
            socketio.emit("admin:blog:post:updated", event_data, to="admin_room")
        except Exception as exc:
            logger.error("[BlogEventHandlers] Error in blog.post.updated handler: %r", exc)

    def _on_post_deleted(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info("[BlogEventHandlers] blog.post.deleted: %s", event_data.get("id"))
            from tuned.extensions import socketio
            socketio.emit("admin:blog:post:deleted", event_data, to="admin_room")
        except Exception as exc:
            logger.error("[BlogEventHandlers] Error in blog.post.deleted handler: %r", exc)

    def _on_post_published(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info("[BlogEventHandlers] blog.post.published: %s", event_data.get("id"))
            from tuned.extensions import socketio
            socketio.emit("admin:blog:post:published", event_data, to="admin_room")
        except Exception as exc:
            logger.error("[BlogEventHandlers] Error in blog.post.published handler: %r", exc)

    def _on_category_created(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info("[BlogEventHandlers] blog.category.created: %s", event_data.get("id"))
            from tuned.extensions import socketio
            socketio.emit("admin:blog:category:created", event_data, to="admin_room")
        except Exception as exc:
            logger.error("[BlogEventHandlers] Error in blog.category.created handler: %r", exc)

    def _on_category_updated(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info("[BlogEventHandlers] blog.category.updated: %s", event_data.get("id"))
            from tuned.extensions import socketio
            socketio.emit("admin:blog:category:updated", event_data, to="admin_room")
        except Exception as exc:
            logger.error("[BlogEventHandlers] Error in blog.category.updated handler: %r", exc)

    def _on_category_deleted(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info("[BlogEventHandlers] blog.category.deleted: %s", event_data.get("id"))
            from tuned.extensions import socketio
            socketio.emit("admin:blog:category:deleted", event_data, to="admin_room")
        except Exception as exc:
            logger.error("[BlogEventHandlers] Error in blog.category.deleted handler: %r", exc)

    def _on_comment_updated(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info("[BlogEventHandlers] blog.comment.updated: %s", event_data.get("id"))
            from tuned.extensions import socketio
            socketio.emit("admin:blog:comment:updated", event_data, to="admin_room")
        except Exception as exc:
            logger.error("[BlogEventHandlers] Error in blog.comment.updated handler: %r", exc)
