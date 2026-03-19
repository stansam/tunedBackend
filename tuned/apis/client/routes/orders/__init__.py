"""
Order routes initialization.

Imports all order-related route modules.
"""

# Order management
from tuned.client.routes.orders import create, get

# Order activities
from tuned.client.routes.orders.activities import (
    comments,
    extend_deadline,
    support,
    revisions,
    delivery
)

# File management
from tuned.client.routes.orders.activities import files
