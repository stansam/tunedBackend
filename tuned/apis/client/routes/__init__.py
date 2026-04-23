from tuned.apis.client.routes.dashboard import (
    NavStats,
    DashboardKPIs,
    DashboardAnalytics,
    DashboardTracking,
    DashboardAlerts
)
from tuned.apis.client.routes.orders import ReorderOrder

CLIENT_ROUTES = [
    {
        "rule": "/nav-stats",
        "view_func": NavStats.as_view("client_nav_stats"),
        "methods": ["GET"],
    },
    {
        "rule": "/dashboard/kpis",
        "view_func": DashboardKPIs.as_view("dashboard_kpis"),
        "methods": ["GET"],
    },
    {
        "rule": "/dashboard/analytics",
        "view_func": DashboardAnalytics.as_view("dashboard_analytics"),
        "methods": ["GET"],
    },
    {
        "rule": "/dashboard/tracking",
        "view_func": DashboardTracking.as_view("dashboard_tracking"),
        "methods": ["GET"],
    },
    {
        "rule": "/dashboard/alerts",
        "view_func": DashboardAlerts.as_view("dashboard_alerts"),
        "methods": ["GET"],
    },
    {
        "rule": "/orders/<string:order_id>/reorder",
        "view_func": ReorderOrder.as_view("order_reorder"),
        "methods": ["POST"],
    },
]
