from tuned.apis.main.routes.homepage import(
    GetFeaturedContent, GetQuoteFormOptions, CalculatePrice, NewsletterSubscribeView,
    GlobalSearchView
)
from tuned.apis.main.routes.services.list import(
    GetServicesList, GetServicesBySlug, GetServicesByCategory,
    GetServiceCategoriesList, GetServicesRelated
)
from tuned.apis.main.routes.blogs import(
    ListBlogPosts, GetBlogPost, GetBlogComments,
    ListBlogCategories, GetRelatedBlogPosts
)
from tuned.apis.main.routes.content import(
    GetAcademicLevels, SampleListView, SampleDetailView,
    SampleServiceView, SampleRelatedView, GetTagsList,
    TestimonialsView
)


from typing import Any

ROUTES: list[dict[str, Any]] = [
    {"url_rule": "/featured/contents", "view_func": GetFeaturedContent.as_view("featured_contents"), 'methods': ['GET']},
    {"url_rule": "/quote/options", "view_func": GetQuoteFormOptions.as_view("quote_form_options"), 'methods': ['GET']},
    {"url_rule": "/calculate-price", "view_func": CalculatePrice.as_view("calculate_price"), 'methods': ['POST']},
    {"url_rule": "/testimonials", "view_func": TestimonialsView.as_view("testimonials_list"), 'methods': ['GET']},
    {"url_rule": "/newsletter/subscribe", "view_func": NewsletterSubscribeView.as_view("newsletter_subscribe"), 'methods': ['POST']},
    {"url_rule": "/search", "view_func": GlobalSearchView.as_view("global_search"), 'methods': ['GET']},

    {"url_rule": "/services", "view_func": GetServicesList.as_view("services"), 'methods': ['GET']},
    {"url_rule": "/services/<string:slug>", "view_func": GetServicesBySlug.as_view("service_by_slug"), 'methods': ['GET']},
    {"url_rule": "/services/category/<string:category_id>", "view_func": GetServicesByCategory.as_view("services_by_category"), 'methods': ['GET']},
    {"url_rule": "/services/categories", "view_func": GetServiceCategoriesList.as_view("services_categories"), 'methods': ['GET']},
    {"url_rule": "/services/<string:slug>/related", "view_func": GetServicesRelated.as_view("services_related"), 'methods': ['GET']},

    {"url_rule": "/academic-levels", "view_func": GetAcademicLevels.as_view("academic_levels"), 'methods': ['GET']},
    {"url_rule": "/tags", "view_func": GetTagsList.as_view("tags_list"), 'methods': ['GET']},

    {"url_rule": "/blogs", "view_func": ListBlogPosts.as_view("blogs"), 'methods': ['GET']},
    {"url_rule": "/blogs/<string:slug>/related", "view_func": GetRelatedBlogPosts.as_view("blogs_related"), 'methods': ['GET']},
    {"url_rule": "/blogs/<string:slug>", "view_func": GetBlogPost.as_view("blog"), 'methods': ['GET']},
    {"url_rule": "/blogs/<string:slug>/comments", "view_func": GetBlogComments.as_view("blog_comments"), 'methods': ['GET']},

    {"url_rule": "/blogs/categories", "view_func": ListBlogCategories.as_view("blog_categories"), 'methods': ['GET']},
    
    {"url_rule": "/samples", "view_func": SampleListView.as_view("samples"), 'methods': ['GET']},
    {"url_rule": "/samples/<string:slug>", "view_func": SampleDetailView.as_view("sample_detail"), 'methods': ['GET']},
    {"url_rule": "/samples/services", "view_func": SampleServiceView.as_view("sample_services"), 'methods': ['GET']},
    {"url_rule": "/samples/<string:slug>/related", "view_func": SampleRelatedView.as_view("sample_related"), 'methods': ['GET']},
]