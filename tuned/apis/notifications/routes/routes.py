from dataclasses import asdict
from flask import Blueprint, request
from flask.views import MethodView
from flask_login import login_required, current_user
from tuned.utils.dependencies import get_services
from tuned.repository.exceptions import DatabaseError, NotFound
from tuned.utils.responses import success_response, error_response
import logging
from typing import Any

logger = logging.getLogger(__name__)


class NotificationListAPI(MethodView):
    decorators = [login_required]

    def get(self) -> tuple[Any, int]:
        try:
            user_id = current_user.id
            raw_limit = request.args.get('limit', '20')
            raw_offset = request.args.get('offset', '0')
            
            try:
                limit = max(1, min(int(raw_limit), 100))
                offset = max(0, int(raw_offset))
            except ValueError as e:
                logger.error(f"Invalid notification pagination request: {e}")
                return error_response("limit and offset must be non-negative integers", status=400)
            
            services = get_services()
            notifications = services.notification.get_user_notifications(str(user_id), limit, offset)
            total = services.notification.get_total_count(str(user_id))
            
            return success_response({
                "notifications": [asdict(item) for item in notifications],
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total,
            })
        except DatabaseError as e:
            logger.error(f"Error fetching notifications: {e}")
            return error_response("Failed to fetch notifications", status=500)
        except Exception as e:
            logger.error(f"Error fetching notifications: {e}")
            return error_response("Failed to fetch notifications", status=500)

class NotificationReadAPI(MethodView):
    decorators = [login_required]

    def put(self, notification_id: str) -> tuple[Any, int]:
        try:
            user_id = current_user.id
            notification = get_services().notification.mark_read(notification_id, str(user_id))
            return success_response({"notification": asdict(notification)})
        except NotFound:
            return error_response("Notification not found", status=404)
        except DatabaseError as e:
            logger.error(f"Error marking notification read: {e}")
            return error_response("Failed to mark read", status=500)
        except Exception as e:
            logger.error(f"Error marking notification read: {e}")
            return error_response("Failed to mark read", status=500)

class NotificationReadAllAPI(MethodView):
    decorators = [login_required]

    def put(self) -> tuple[Any, int]:
        try:
            user_id = current_user.id
            updated_count = get_services().notification.mark_all_read(str(user_id))
            return success_response({"updated_count": updated_count})
        except DatabaseError as e:
            logger.error(f"Error marking all notifications read: {e}")
            return error_response("Failed to mark all read", status=500)
        except Exception as e:
            logger.error(f"Error marking all notifications read: {e}")
            return error_response("Failed to mark all read", status=500)

class NotificationDeleteAPI(MethodView):
    decorators = [login_required]

    def delete(self, notification_id: str) -> tuple[Any, int]:
        try:
            user_id = current_user.id
            get_services().notification.delete_notification(notification_id, str(user_id))
            return success_response({"deleted_id": notification_id})
        except NotFound:
            return error_response("Notification not found", status=404)
        except DatabaseError as e:
            logger.error(f"Error deleting notification: {e}")
            return error_response("Failed to delete", status=500)
        except Exception as e:
            logger.error(f"Error deleting notification: {e}")
            return error_response("Failed to delete", status=500)