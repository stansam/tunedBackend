"""
Order activities routes initialization.

Imports all order activity-related route modules.
"""

# Import activity modules - these will register their routes when imported
try:
    from tuned.client.routes.orders.activities.comments import __init__ as comments
except ImportError:
    pass

try:
    from tuned.client.routes.orders.activities import extend_deadline
except ImportError:
    pass

try:
    from tuned.client.routes.orders.activities import support
except ImportError:
    pass

try:
    from tuned.client.routes.orders.activities import revisions
except ImportError:
    pass

try:
    from tuned.client.routes.orders.activities import delivery
except ImportError:
    pass

try:
    from tuned.client.routes.orders.activities.files import __init__ as files
except ImportError:
    pass
