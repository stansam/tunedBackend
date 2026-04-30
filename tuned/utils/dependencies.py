from flask import current_app
from tuned.interface import Services

def get_services() -> Services:
    services = current_app.extensions.get('services')
    if services is None:
        raise RuntimeError("Services not initialized. Was create_app() called?")
    return services
