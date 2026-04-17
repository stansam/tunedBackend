import eventlet
eventlet.monkey_patch() 

from tuned import create_app
from tuned.extensions import socketio
# from tuned.core.events.bootstrap import init_events
from tuned.celery_app import init_celery

app = create_app()
init_celery(app)
# init_events()

if __name__ == '__main__':
    socketio.run(
        app,
        debug=True,
        host='0.0.0.0',
        port=5000,
        use_reloader=True
    )
