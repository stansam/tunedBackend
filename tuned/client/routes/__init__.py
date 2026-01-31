"""
Client blueprint routes initialization.

This module imports all client route modules to register them with the blueprint.
All routes are automatically registered when imported.
"""

# Order routes
from tuned.client.routes import orders

# Payment routes  
from tuned.client.routes import payments

# Settings routes
from tuned.client.routes import settings

# Referral routes
from tuned.client.routes import referrals


__all__ = [
    'orders',
    'payments',
    'settings',
    'referrals'
]
