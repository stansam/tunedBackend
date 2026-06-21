from typing import Any
from tuned.apis.admin.routes.nav_stats import AdminNavStatsView
from tuned.apis.admin.routes.dashboard import (
    AdminKPIView, AdminAnalyticsView, AdminTrackingView, AdminAlertsView
)
from tuned.apis.admin.routes.orders import (
    AdminOrdersListView, AdminOrdersStatsView,
    AdminActivateOrderView, AdminEscalateOrderView
)
from tuned.apis.admin.routes.order_detail import (
    AdminOrderDetailView, AdminOrderRevisionRequestsView, AdminUpdateRevisionStatusView
)
from tuned.apis.admin.routes.order_extensions import AdminDeadlineExtensionsView
from tuned.apis.admin.routes.users import (
    AdminUsersListView, AdminUsersStatsView, AdminUsersGeographyView,
    AdminBroadcastView, AdminMessageUserView, AdminUsersExportView
)
from tuned.apis.admin.routes.payments import AdminPaymentsListView
from tuned.apis.admin.routes.services import (
    AdminServiceCategoriesListView, AdminPricingCategoriesListView
)
from tuned.apis.admin.routes.services_list import AdminServicesListView
from tuned.apis.admin.routes.services_detail import (
    AdminServiceCategoryDetailView, AdminServiceDetailView
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
        "url_rule": "/orders/detail/<string:order_number>",
        "view_func": AdminOrderDetailView.as_view("admin_order_detail"),
        "methods": ["GET"],
    },
    {
        "url_rule": "/orders/<string:order_id>/revision-requests",
        "view_func": AdminOrderRevisionRequestsView.as_view("admin_order_revision_requests"),
        "methods": ["GET"],
    },
    {
        "url_rule": "/orders/<string:order_id>/revision-requests/<string:request_id>/status",
        "view_func": AdminUpdateRevisionStatusView.as_view("admin_update_revision_status"),
        "methods": ["PATCH"],
    },
    {
        "url_rule": "/orders/<string:order_id>/deadline-extensions",
        "view_func": AdminDeadlineExtensionsView.as_view("admin_deadline_extensions"),
        "methods": ["GET", "POST"],
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
    {
        "url_rule": "/payments/list",
        "view_func": AdminPaymentsListView.as_view("admin_payments_list"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/services/categories",
        "view_func": AdminServiceCategoriesListView.as_view("admin_service_categories_list"),
        "methods": ["GET", "POST"],
    },
    {
        "url_rule": "/services/categories/<string:category_id>",
        "view_func": AdminServiceCategoryDetailView.as_view("admin_service_category_detail"),
        "methods": ["PUT", "DELETE"],
    },
    {
        "url_rule": "/services",
        "view_func": AdminServicesListView.as_view("admin_services_list"),
        "methods": ["GET", "POST"],
    },
    {
        "url_rule": "/services/<string:service_id>",
        "view_func": AdminServiceDetailView.as_view("admin_service_detail"),
        "methods": ["PUT", "DELETE"],
    },
    {
        "url_rule": "/pricing-categories",
        "view_func": AdminPricingCategoriesListView.as_view("admin_pricing_categories_list"),
        "methods": ["GET"],
    },
]

