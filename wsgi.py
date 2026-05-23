from gevent import monkey
monkey.patch_all()

from tuned import create_app
from tuned.extensions import socketio

app = create_app()