import os
import logging
from tuned import create_app
from tuned.celery_app import celery_app, init_celery
from tuned.core.events.bootstrap import init_events

flask_app = create_app(os.environ.get("FLASK_ENV", "development"))

if not flask_app.config.get('SOCKETIO_MESSAGE_QUEUE'):
    logging.getLogger("celery").warning(
        "[Celery] SOCKETIO_MESSAGE_QUEUE is not configured. "
        "Task emissions to SocketIO clients will be silently discarded."
    )

init_celery(flask_app)
with flask_app.app_context():
    init_events()

flask_app.extensions["celery"] = celery_app