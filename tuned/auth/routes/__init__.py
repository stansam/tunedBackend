"""
Auth routes package.

Registers all authentication routes with the auth blueprint.
"""
from tuned.auth.routes import register, login, logout, verify_email, password_reset


# Routes are automatically registered when imported
# Flask blueprint decorator handles route registration
