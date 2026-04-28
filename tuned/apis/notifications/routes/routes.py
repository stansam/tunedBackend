from dataclasses import asdict
from flask import Blueprint, request
from flask.views import MethodView
from flask_login import login_required, current_user
from tuned.interface import notification as notification_interface
from tuned.repository.exceptions import DatabaseError, NotFound
from tuned.utils.responses import success_response, error_response
import logging
from typing import Any

logger = logging.getLogger(__name__)

bp = Blueprint('notifications', __name__, url_prefix='/notifications')

class NotificationListAPI(MethodView):
    decorators = [login_required]

    def get(self) -> tuple[Any, int]:
        try:
            user_id = current_user.id
            limit = int(request.args.get('limit', 20))
            offset = int(request.args.get('offset', 0))
            
            notifications = notification_interface.get_user_notifications(str(user_id), limit, offset)
            return success_response([asdict(item) for item in notifications])
        except ValueError as e:
            logger.error(f"Invalid notification pagination request: {e}")
            return error_response("Invalid pagination parameters", status=400)
        except DatabaseError as e:
            logger.error(f"Error fetching notifications: {e}")
            return error_response("Failed to fetch notifications", status=500)
        except Exception as e:
            logger.error(f"Error fetching notifications: {e}")
            return error_response("Failed to fetch notifications", status=500)

class NotificationReadAPI(MethodView):
    decorators = [login_required]

    def post(self, notification_id: str) -> tuple[Any, int]:
        try:
            user_id = current_user.id
            notification = notification_interface.mark_read(str(notification_id), str(user_id))
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

    def post(self) -> tuple[Any, int]:
        try:
            user_id = current_user.id
            updated_count = notification_interface.mark_all_read(str(user_id))
            return success_response({"updated_count": updated_count})
        except DatabaseError as e:
            logger.error(f"Error marking all notifications read: {e}")
            return error_response("Failed to mark all read", status=500)
        except Exception as e:
            logger.error(f"Error marking all notifications read: {e}")
            return error_response("Failed to mark all read", status=500)

bp.add_url_rule('', view_func=NotificationListAPI.as_view('list'))
bp.add_url_rule('/<notification_id>/read', view_func=NotificationReadAPI.as_view('read'))
bp.add_url_rule('/read-all', view_func=NotificationReadAllAPI.as_view('read_all'))
