from tuned.apis.main.routes.homepage import(
    GetFeaturedContent, GetQuoteFormOptions, CalculatePrice
)
from tuned.apis.main.routes.services.list import(
    GetServicesList, GetServicesBySlug, GetServicesByCategory,
    GetServiceCategoriesList, GetServicesRelated
)
from tuned.apis.main.routes.content import(
    GetAcademicLevels
)

ROUTES = [
    {"url_rule": "/featured/contents", "view_func": GetFeaturedContent.as_view("featured_contents")},
    {"url_rule": "/quote/options", "view_func": GetQuoteFormOptions.as_view("quote_form_options")},
    {"url_rule": "/calculate-price", "view_func": CalculatePrice.as_view("calculate_price")},

    {"url_rule": "/services", "view_func": GetServicesList.as_view("services")},
    {"url_rule": "/services/<string:slug>", "view_func": GetServicesBySlug.as_view("service_by_slug")},
    {"url_rule": "/services/category/<string:category_id>", "view_func": GetServicesByCategory.as_view("services_by_category")},
    {"url_rule": "/services/categories", "view_func": GetServiceCategoriesList.as_view("services_categories")},
    {"url_rule": "/services/<string:slug>/related", "view_func": GetServicesRelated.as_view("services_related")},

    {"url_rule": "/academic-levels", "view_func": GetAcademicLevels.as_view("academic_levels")},
]