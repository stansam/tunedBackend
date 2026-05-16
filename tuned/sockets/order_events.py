from __future__ import annotations
from flask_login import current_user
from flask_socketio import join_room, leave_room
from tuned.extensions import socketio
from tuned.core.logging import get_logger
import logging
from typing import Any

logger: logging.Logger = get_logger(__name__)

@socketio.on("join:order")
def handle_join_order(data: dict[str, Any]) -> None:
    if not current_user.is_authenticated:
        return
    order_id = data.get("orderId")
    if not order_id:
        return
    room = f"order_{order_id}"
    join_room(room)
    logger.debug("[OrderSocket] User %s joined room %s", current_user.id, room)

@socketio.on("leave:order")
def handle_leave_order(data: dict[str, Any]) -> None:
    if not current_user.is_authenticated:
        return
    order_id = data.get("orderId")
    if not order_id:
        return
    room = f"order_{order_id}"
    leave_room(room)
    logger.debug("[OrderSocket] User %s left room %s", current_user.id, room)
