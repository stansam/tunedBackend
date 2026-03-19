"""Homepage routes package."""
from tuned.apis.main.routes.homepage.featured import GetFeaturedContent
from tuned.apis.main.routes.homepage.quote_form import GetQuoteFormOptions, CalculatePrice
#  (
#     featured,
#     quote_form,
#     search,
#     testimonials,
#     newsletter_subscribe
# )

__all__ = [
    'GetFeaturedContent',
    'GetQuoteFormOptions',
    'CalculatePrice',
]
