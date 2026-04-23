from tuned.apis.client.routes.dashboard import (
    NavStats,
    DashboardKPIs,
    DashboardAnalytics,
    DashboardTracking,
    DashboardAlerts
)
from tuned.apis.client.routes.orders import ReorderOrder
from tuned.apis.client.routes.profile import (
    ProfileView,
    AvatarUploadView,
    VerifyEmailView,
    ChangePasswordView
)

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
    {
        "rule": "/profile",
        "view_func": ProfileView.as_view("profile_view"),
        "methods": ["GET", "PATCH"],
    },
    {
        "rule": "/profile/avatar",
        "view_func": AvatarUploadView.as_view("avatar_upload_view"),
        "methods": ["POST", "DELETE"],
    },
    {
        "rule": "/profile/verify-email",
        "view_func": VerifyEmailView.as_view("verify_email_view"),
        "methods": ["POST"],
    },
    {
        "rule": "/profile/change-password",
        "view_func": ChangePasswordView.as_view("change_password_view"),
        "methods": ["POST"],
    },
]
