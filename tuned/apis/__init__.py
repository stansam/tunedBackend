from tuned.apis.main import main_bp
from tuned.apis.auth import auth_bp
from tuned.apis.notifications import notification_bp
from tuned.apis.client import client_bp
from tuned.apis.orders import orders_bp
from tuned.apis.order_deliveries import order_deliveries_bp
from tuned.apis.payments import payments_bp
from tuned.apis.media import media_bp
from tuned.apis.admin import admin_bp

__all__ = [
    'main_bp',
    'auth_bp',
    'notification_bp',
    'client_bp',
    'orders_bp',
    'order_deliveries_bp',
    'payments_bp',
    'media_bp',
    'admin_bp',
]