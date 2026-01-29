"""
Sockets package.

Registers all Socket.IO event handlers.
"""
from tuned.sockets import notification_events

# Events are automatically registered when imported
# SocketIO decorators handle event registration

__all__ = ['notification_events']
