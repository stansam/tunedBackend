from __future__ import annotations

from celery import Celery
from tuned.core.config import config
import os


def make_celery(flask_app=None) -> Celery:
    config_name = os.environ.get('FLASK_ENV', 'development')
    flask_config = config[config_name]

    celery = Celery(
        'tuned',
        broker=flask_config.CELERY_BROKER_URL,
        backend=flask_config.CELERY_RESULT_BACKEND,
        include=[
            'tuned.tasks.email',
            'tuned.tasks.notifications',
            'tuned.tasks.order_tasks',
        ],
    )

    celery.conf.update(
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
        },
        broker_transport_options={
            'visibility_timeout': 3600,  # 1 hour
        },
    )

    if flask_app is not None:
        class ContextTask(celery.Task):
            _flask_app = flask_app

            def __call__(self, *args, **kwargs):
                with self._flask_app.app_context():
                    return self.run(*args, **kwargs)

        celery.Task = ContextTask

    return celery

celery_app = make_celery()
