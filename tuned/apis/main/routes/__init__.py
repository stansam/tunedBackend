from tuned.apis.main.routes.homepage import(
    GetFeaturedContent, GetQuoteFormOptions, CalculatePrice
)
from tuned.apis.main.routes.services.list import(
    GetServicesList, GetServicesBySlug, GetServicesByCategory,
    GetServiceCategoriesList, GetServicesRelated
)
from tuned.apis.main.routes.blogs import(
    ListBlogPosts, GetBlogPost, GetBlogComments,
    ListBlogCategories
)
from tuned.apis.main.routes.content import(
    GetAcademicLevels, SampleListView
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

    {"url_rule": "/blogs", "view_func": ListBlogPosts.as_view("blogs")},
    {"url_rule": "/blogs/<string:slug>", "view_func": GetBlogPost.as_view("blog")},
    {"url_rule": "/blogs/<string:slug>/comments", "view_func": GetBlogComments.as_view("blog_comments")},

    {"url_rule": "/blogs/categories", "view_func": ListBlogCategories.as_view("blog_categories")},
    
    {"url_rule": "/samples", "view_func": SampleListView.as_view("samples")},
]