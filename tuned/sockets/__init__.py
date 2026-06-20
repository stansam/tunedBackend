from __future__ import annotations
from typing import Any


def init_sockets(socketio: Any) -> None:
    """
    Register TunedNamespace at the root namespace.
    Must be called from create_app() AFTER socketio.init_app().
    """
    from tuned.sockets.namespace import TunedNamespace
    socketio.on_namespace(TunedNamespace("/"))

    import logging
    logging.getLogger(__name__).info("[Sockets] TunedNamespace registered at '/'")


__all__ = ["init_sockets"]
