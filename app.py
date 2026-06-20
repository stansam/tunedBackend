from gevent import monkey
monkey.patch_all() 

from tuned import create_app
from tuned.extensions import socketio

app = create_app()

if __name__ == '__main__':
    socketio.run(
        app,
        debug=app.debug,
        host='0.0.0.0',
        port=5000,
        use_reloader=True,
        ping_timeout=60,
        ping_interval=25
    )
