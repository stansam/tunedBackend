from gevent import monkey
monkey.patch_all()

from tuned import create_app
from tuned.extensions import socketio

app = create_app()

if __name__ == '__main__':
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=app.debug
    )