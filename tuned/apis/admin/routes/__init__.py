from tuned.apis.admin.routes.nav_stats import AdminNavStatsView

ADMIN_ROUTES = [
    {
        "url_rule": "/nav-stats",
        "view_func": AdminNavStatsView.as_view("admin_nav_stats"),
        "methods": ["GET"],
    },
]
