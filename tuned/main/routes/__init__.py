from tuned.main.routes.homepage import(
    GetFeaturedContent, GetQuoteFormOptions
)

ROUTES = [
    {"url_rule": "/featured", "view_func": GetFeaturedContent.as_view("featured")},
    {"url_rule": "/quote/options", "view_func": GetQuoteFormOptions.as_view("quote_form_options")}
]