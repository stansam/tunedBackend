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
from tuned.apis.admin.routes.blogs import (
    AdminBlogStatsView, AdminBlogPostsListView, AdminBlogPostsCollectionView,
    AdminBlogPostDetailView, AdminBlogPostPublishView, AdminBlogPostFeatureView,
    AdminBlogPostCommentsView, AdminBlogCategoriesListView, AdminBlogCategoryDetailView,
    AdminBlogCommentApproveView, AdminBlogCommentDetailView, AdminBlogReactionDetailView,
)
from tuned.apis.admin.routes.samples import AdminSamplesListView, AdminSampleDetailView
from tuned.apis.admin.routes.testimonials import (
    AdminTestimonialsListView, AdminTestimonialApproveView, AdminTestimonialDetailView
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
    {
        "url_rule": "/samples",
        "view_func": AdminSamplesListView.as_view("admin_samples_list"),
        "methods": ["GET", "POST"],
    },
    {
        "url_rule": "/samples/<string:sample_id>",
        "view_func": AdminSampleDetailView.as_view("admin_sample_detail"),
        "methods": ["PUT", "DELETE"],
    },
    {
        "url_rule": "/testimonials",
        "view_func": AdminTestimonialsListView.as_view("admin_testimonials_list"),
        "methods": ["GET"],
    },
    {
        "url_rule": "/testimonials/<string:testimonial_id>/approve",
        "view_func": AdminTestimonialApproveView.as_view("admin_testimonial_approve"),
        "methods": ["PATCH"],
    },
    {
        "url_rule": "/testimonials/<string:testimonial_id>",
        "view_func": AdminTestimonialDetailView.as_view("admin_testimonial_detail"),
        "methods": ["PUT", "DELETE"],
    },
    # ── Blogs ──────────────────────────────────────────────────────────────
    {
        "url_rule": "/blogs/stats",
        "view_func": AdminBlogStatsView.as_view("admin_blog_stats"),
        "methods": ["GET"],
    },
    {
        "url_rule": "/blogs/list",
        "view_func": AdminBlogPostsListView.as_view("admin_blog_posts_list"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/blogs/posts",
        "view_func": AdminBlogPostsCollectionView.as_view("admin_blog_posts_collection"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/blogs/posts/<string:slug>",
        "view_func": AdminBlogPostDetailView.as_view("admin_blog_post_detail"),
        "methods": ["GET", "PATCH", "DELETE"],
    },
    {
        "url_rule": "/blogs/posts/<string:post_id>/publish",
        "view_func": AdminBlogPostPublishView.as_view("admin_blog_post_publish"),
        "methods": ["PATCH"],
    },
    {
        "url_rule": "/blogs/posts/<string:post_id>/feature",
        "view_func": AdminBlogPostFeatureView.as_view("admin_blog_post_feature"),
        "methods": ["PATCH"],
    },
    {
        "url_rule": "/blogs/posts/<string:post_id>/comments",
        "view_func": AdminBlogPostCommentsView.as_view("admin_blog_post_comments"),
        "methods": ["GET"],
    },
    {
        "url_rule": "/blogs/categories",
        "view_func": AdminBlogCategoriesListView.as_view("admin_blog_categories_list"),
        "methods": ["GET", "POST"],
    },
    {
        "url_rule": "/blogs/categories/<string:category_id>",
        "view_func": AdminBlogCategoryDetailView.as_view("admin_blog_category_detail"),
        "methods": ["PATCH", "DELETE"],
    },
    {
        "url_rule": "/blogs/comments/<string:comment_id>/approve",
        "view_func": AdminBlogCommentApproveView.as_view("admin_blog_comment_approve"),
        "methods": ["PATCH"],
    },
    {
        "url_rule": "/blogs/comments/<string:comment_id>",
        "view_func": AdminBlogCommentDetailView.as_view("admin_blog_comment_detail"),
        "methods": ["DELETE"],
    },
    {
        "url_rule": "/blogs/reactions/<string:reaction_id>",
        "view_func": AdminBlogReactionDetailView.as_view("admin_blog_reaction_detail"),
        "methods": ["DELETE"],
    },
]
