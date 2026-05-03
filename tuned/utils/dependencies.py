from typing import cast, TYPE_CHECKING
from flask import current_app, has_app_context

if TYPE_CHECKING:
    from tuned.interface import Services

def get_services() -> "Services":
    # services = cast(Services, current_app.extensions.get('services'))
    if not has_app_context():
        raise RuntimeError("No Flask application context found.")
    services = current_app.extensions.get('services')
    if services is None:
        raise RuntimeError("Services not initialized. Was create_app() called?")
    return cast("Services", services)
