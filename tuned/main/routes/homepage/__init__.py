"""Homepage routes package."""
from tuned.main.routes.homepage.featured import GetFeaturedContent
from tuned.main.routes.homepage.quote_form import GetQuoteFormOptions
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
    # 'quote_form',
    # 'search',
    # 'testimonials',
    # 'newsletter_subscribe',
]
