from __future__ import annotations

import os
from celery import Celery, Task
from flask import has_app_context
from tuned.core.config import config

flask_app_instance = None

class ContextTask(Task):
    def __call__(self, *args, **kwargs):
        # if has_app_context():
        #     return self.run(*args, **kwargs)
        
        # global flask_app_instance
        # if flask_app_instance is None:
        #     from tuned import create_app
        #     flask_env = os.environ.get('FLASK_ENV', 'development')
        #     flask_app_instance = create_app(flask_env)
            # raise RuntimeError("Celery app not initialized with Flask app")
            
        with flask_app_instance.app_context():
            return self.run(*args, **kwargs)

config_name = os.environ.get('FLASK_ENV', 'development')
flask_config = config[config_name]

celery_app = Celery(
    'tuned',
    broker=flask_config.CELERY_BROKER_URL,
    backend=flask_config.CELERY_RESULT_BACKEND,
    task_cls=ContextTask,
    include=[
        'tuned.tasks.email',
        'tuned.tasks.notifications',
        'tuned.tasks.order_tasks',
        'tuned.tasks.dashboard_tasks',
    ],
)

celery_app.conf.update(
    task_serializer=flask_config.CELERY_TASK_SERIALIZER,
    result_serializer=flask_config.CELERY_RESULT_SERIALIZER,
    accept_content=flask_config.CELERY_ACCEPT_CONTENT,
    timezone=flask_config.CELERY_TIMEZONE,
    enable_utc=flask_config.CELERY_ENABLE_UTC,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_routes={
        'tuned.tasks.email.*': {'queue': 'email'},
        'tuned.tasks.notifications.*': {'queue': 'notifications'},
        'tuned.tasks.order_tasks.*': {'queue': 'orders'},
        'tuned.tasks.dashboard_tasks.*': {'queue': 'notifications'},
    },
    broker_transport_options={
        'visibility_timeout': 3600,  # 1 hour
    },
)

def init_celery(app):
    global flask_app_instance
    flask_app_instance = app
