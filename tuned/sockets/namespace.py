from __future__ import annotations

import logging
from functools import wraps
from typing import Any, Callable

from flask_socketio import Namespace, emit, join_room, leave_room
from flask_login import current_user

from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)


def socket_login_required(f: Callable) -> Callable:
    """
    Decorator for Namespace methods: emits error and returns early
    if the current socket connection is not authenticated.
    """
    @wraps(f)
    def wrapper(self: TunedNamespace, *args: Any, **kwargs: Any) -> Any:
        if not current_user or not current_user.is_authenticated:
            logger.warning(
                "[Socket] Unauthenticated call to %s from SID %s",
                f.__name__, getattr(self, "sid", "unknown")
            )
            emit("error", {"code": 401, "message": "Unauthorized"})
            return
        return f(self, *args, **kwargs)
    return wrapper


class TunedNamespace(Namespace):
    """
    Single authoritative Flask-SocketIO Namespace for the tuned platform.

    Handles:
    - Connection lifecycle (connect / disconnect)
    - User room management (user_{id}, admin_room)
    - Dashboard subscription / unsubscription
    - Order room join / leave
    - Notification mark-read and unread-count queries

    Domain-specific server-push events (order.updated, notification:new, etc.)
    are emitted to rooms by interface/*/events.py handlers via socketio.emit().
    This class only handles CLIENT-INITIATED socket events.
    """

    # -----------------------------------------------------------------------
    # Lifecycle
    # -----------------------------------------------------------------------

    def on_connect(self) -> bool:
        try:
            if not current_user or not current_user.is_authenticated:
                logger.warning("[Socket] Unauthenticated connection attempt")
                return False

            user_id   = str(current_user.id)
            user_room = f"user_{user_id}"
            join_room(user_room)
            logger.info("[Socket] User %s connected → joined %s", user_id, user_room)

            if getattr(current_user, "is_admin", False):
                join_room("admin_room")
                logger.info("[Socket] Admin %s joined admin_room", user_id)

            # Push unread count asynchronously to avoid blocking connect
            try:
                from tuned.tasks.notifications import push_unread_count_task
                push_unread_count_task.apply_async(args=[user_id], countdown=0)
            except Exception as exc:
                # Fallback: emit synchronously if Celery task unavailable
                logger.warning("[Socket] push_unread_count_task unavailable: %r — falling back", exc)
                try:
                    from tuned.utils.dependencies import get_services
                    unread = get_services().notification.get_unread_count(user_id)
                    emit("notification:count", {"unread_count": unread})
                except Exception as fb_exc:
                    logger.error("[Socket] Fallback unread count failed: %r", fb_exc)

            return True

        except Exception as exc:
            logger.error("[Socket] Connect error: %r", exc)
            return False

    def on_disconnect(self) -> None:
        try:
            if current_user and current_user.is_authenticated:
                logger.info("[Socket] User %s disconnected", current_user.id)
            else:
                logger.debug("[Socket] Unauthenticated client disconnected")
        except Exception as exc:
            logger.debug("[Socket] Disconnect cleanup error: %r", exc)

    # -----------------------------------------------------------------------
    # Dashboard room management
    # -----------------------------------------------------------------------

    @socket_login_required
    def on_dashboard__subscribe(self, data: dict[str, Any]) -> None:
        """Client subscribes to personal dashboard room. (Already joined on connect.)"""
        room = f"user_{current_user.id}"
        logger.debug("[Socket] User %s confirmed dashboard subscription in %s", current_user.id, room)
        emit("dashboard:subscribed", {"room": room})

    @socket_login_required
    def on_dashboard__unsubscribe(self, data: dict[str, Any]) -> None:
        """Client leaves personal dashboard room."""
        room = f"user_{current_user.id}"
        leave_room(room)
        logger.debug("[Socket] User %s left dashboard room %s", current_user.id, room)
        emit("dashboard:unsubscribed", {"room": room})

    # -----------------------------------------------------------------------
    # Order room management
    # -----------------------------------------------------------------------

    @socket_login_required
    def on_join__order(self, data: dict[str, Any]) -> None:
        """
        Client joins a specific order room.
        Validates ownership: only the order's client or an admin may join.
        Accepts both 'orderId' (camelCase) and 'order_id' (snake_case) for frontend compatibility.
        """
        order_id = data.get("orderId") or data.get("order_id")
        if not order_id:
            emit("error", {"code": 400, "message": "order_id required"})
            return

        try:
            from tuned.utils.dependencies import get_services
            order = get_services().order.get_by_id(str(order_id))
        except Exception:
            emit("error", {"code": 404, "message": "Order not found"})
            return

        is_admin  = getattr(current_user, "is_admin", False)
        is_client = str(order.client_id) == str(current_user.id)

        if not is_admin and not is_client:
            logger.warning(
                "[Socket] User %s denied join to order room %s (not owner)",
                current_user.id, order_id
            )
            emit("error", {"code": 403, "message": "Forbidden"})
            return

        room = f"order_{order_id}"
        join_room(room)
        logger.debug("[Socket] User %s joined order room %s", current_user.id, room)
        emit("order:joined", {"order_id": str(order_id)})

    @socket_login_required
    def on_leave__order(self, data: dict[str, Any]) -> None:
        """Client leaves an order room."""
        order_id = data.get("orderId") or data.get("order_id")
        if not order_id:
            return
        room = f"order_{order_id}"
        leave_room(room)
        logger.debug("[Socket] User %s left order room %s", current_user.id, room)
        emit("order:left", {"order_id": str(order_id)})

    # -----------------------------------------------------------------------
    # Notification events
    # -----------------------------------------------------------------------

    @socket_login_required
    def on_notification__mark_read(self, data: dict[str, Any]) -> None:
        notification_id = data.get("notification_id")
        if not notification_id:
            emit("error", {"code": 400, "message": "notification_id required"})
            return

        from tuned.utils.rate_limit import socket_rate_limit
        if not socket_rate_limit(
            key=f"socket:mark_read:{current_user.id}",
            limit=30,
            window=60,
        ):
            emit("error", {"code": 429, "message": "Rate limit exceeded"})
            return

        try:
            from tuned.utils.dependencies import get_services
            notification = get_services().notification.mark_read(
                str(notification_id), str(current_user.id)
            )
            emit(
                "notification:read",
                {"notification_id": str(notification.id)},
                to=f"user_{current_user.id}",
            )
        except Exception as exc:
            logger.error("[Socket] mark_read error: %r", exc)
            emit("error", {"code": 500, "message": "Internal error"})

    @socket_login_required
    def on_notification__get_unread_count(self, data: dict[str, Any]) -> None:
        from tuned.utils.rate_limit import socket_rate_limit
        if not socket_rate_limit(
            key=f"socket:unread_count:{current_user.id}",
            limit=10,
            window=60,
        ):
            emit("error", {"code": 429, "message": "Rate limit exceeded"})
            return

        try:
            from tuned.utils.dependencies import get_services
            unread = get_services().notification.get_unread_count(str(current_user.id))
            emit("notification:count", {"unread_count": unread})
        except Exception as exc:
            logger.error("[Socket] get_unread_count error: %r", exc)
            emit("error", {"code": 500, "message": "Internal error"})
