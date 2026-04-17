import os
from tuned import create_app
from tuned.celery_app import celery_app, init_celery
from tuned.core.events.bootstrap import init_events

flask_app = create_app(os.environ.get("FLASK_ENV", "development"))

init_celery(flask_app)
init_events()

app = celery_app