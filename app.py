import eventlet
eventlet.monkey_patch() 

from tuned import create_app
from tuned.extensions import socketio

app = create_app()

if __name__ == '__main__':
    socketio.run(
        app,
        debug=True,
        host='0.0.0.0',
        port=5000,
        use_reloader=True
    )
