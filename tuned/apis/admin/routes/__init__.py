from typing import Any
from tuned.apis.admin.routes.nav_stats import AdminNavStatsView
from tuned.apis.admin.routes.dashboard import (
    AdminKPIView, AdminAnalyticsView, AdminTrackingView, AdminAlertsView
)
from tuned.apis.admin.routes.orders import (
    AdminOrdersListView, AdminOrdersStatsView,
    AdminActivateOrderView, AdminEscalateOrderView
)
from tuned.apis.admin.routes.users import (
    AdminUsersListView, AdminUsersStatsView, AdminUsersGeographyView,
    AdminBroadcastView, AdminMessageUserView, AdminUsersExportView
)

ADMIN_ROUTES: list[dict[str, Any]] = [
    {
        "url_rule": "/nav-stats",
        "view_func": AdminNavStatsView.as_view("admin_nav_stats"),
        "methods": ["GET"],
    },
    {
        "url_rule": "/dashboard/kpis",
        "view_func": AdminKPIView.as_view("admin_kpis"),
        "methods": ["GET"],
    },
    {
        "url_rule": "/dashboard/analytics",
        "view_func": AdminAnalyticsView.as_view("admin_analytics"),
        "methods": ["GET"],
    },
    {
        "url_rule": "/dashboard/tracking",
        "view_func": AdminTrackingView.as_view("admin_tracking"),
        "methods": ["GET"],
    },
    {
        "url_rule": "/dashboard/alerts",
        "view_func": AdminAlertsView.as_view("admin_alerts"),
        "methods": ["GET"],
    },
    {
        "url_rule": "/orders/list",
        "view_func": AdminOrdersListView.as_view("admin_orders_list"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/orders/stats",
        "view_func": AdminOrdersStatsView.as_view("admin_orders_stats"),
        "methods": ["GET"],
    },
    {
        "url_rule": "/orders/<string:order_id>/activate",
        "view_func": AdminActivateOrderView.as_view("admin_activate_order"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/orders/<string:order_id>/escalate",
        "view_func": AdminEscalateOrderView.as_view("admin_escalate_order"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/users/list",
        "view_func": AdminUsersListView.as_view("admin_users_list"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/users/stats",
        "view_func": AdminUsersStatsView.as_view("admin_users_stats"),
        "methods": ["GET"],
    },
    {
        "url_rule": "/users/geography",
        "view_func": AdminUsersGeographyView.as_view("admin_users_geo"),
        "methods": ["GET"],
    },
    {
        "url_rule": "/users/broadcast",
        "view_func": AdminBroadcastView.as_view("admin_broadcast"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/users/<string:user_id>/message",
        "view_func": AdminMessageUserView.as_view("admin_msg_user"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/users/export",
        "view_func": AdminUsersExportView.as_view("admin_users_export"),
        "methods": ["GET"],
    },
]
