from tuned.apis.notifications.routes.routes import (
    NotificationListAPI, 
    NotificationReadAllAPI, 
    NotificationReadAPI
)

from typing import Any

ROUTES: list[dict[str, Any]] = [
    {"url_rule": "/", "view_func": NotificationListAPI.as_view('list'), "methods": ["GET"]},
    {"url_rule": "/read-all", "view_func": NotificationReadAllAPI.as_view('read_all'), "methods": ["PUT"]},
    {"url_rule": "/<uuid:notification_id>", "view_func": NotificationReadAPI.as_view('read'), "methods": ["PUT"]}
]