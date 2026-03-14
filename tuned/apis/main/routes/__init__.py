from tuned.apis.main.routes.homepage import(
    GetFeaturedContent, GetQuoteFormOptions, CalculatePrice
)

ROUTES = [
    {"url_rule": "/featured", "view_func": GetFeaturedContent.as_view("featured")},
    {"url_rule": "/quote/options", "view_func": GetQuoteFormOptions.as_view("quote_form_options")},
    {"url_rule": "/calculate-price", "view_func": CalculatePrice.as_view("calculate_price")},
]