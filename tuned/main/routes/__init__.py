"""
Main blueprint routes.

Registers all route modules for the main blueprint.
"""
# Import all route modules to register their routes
from tuned.main.routes import homepage
from tuned.main.routes import services
from tuned.main.routes import samples
from tuned.main.routes import blogs

__all__ = ['homepage', 'services', 'samples', 'blogs']
