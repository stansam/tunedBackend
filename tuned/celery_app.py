"""
Celery configuration and application instance.

This module initializes Celery for background task processing.
Celery workers handle:
- Asynchronous email sending
- Delayed welcome emails (15-30 min after verification)
- Other background tasks

Usage:
    # Start a Celery worker
    celery -A tuned.celery_app worker --loglevel=info
    
    # Start Celery beat (scheduler for periodic tasks)
    celery -A tuned.celery_app beat --loglevel=info
"""
from celery import Celery
from tuned.config import config
import os


def make_celery(app=None):
    """
    Create and configure Celery instance.
    
    Args:
        app: Flask application instance (optional)
        
    Returns:
        Celery: Configured Celery instance
    """
    # Get config name from environment
    config_name = os.environ.get('FLASK_ENV', 'development')
    flask_config = config[config_name]
    
    # Create Celery instance
    celery = Celery(
        'tuned',
        broker=flask_config.CELERY_BROKER_URL,
        backend=flask_config.CELERY_RESULT_BACKEND
    )
    
    # Update Celery config from Flask config
    celery.conf.update(
        task_serializer=flask_config.CELERY_TASK_SERIALIZER,
        result_serializer=flask_config.CELERY_RESULT_SERIALIZER,
        accept_content=flask_config.CELERY_ACCEPT_CONTENT,
        timezone=flask_config.CELERY_TIMEZONE,
        enable_utc=flask_config.CELERY_ENABLE_UTC,
    )
    
    # If Flask app provided, create app context for tasks
    if app:
        class ContextTask(celery.Task):
            """
            Make celery tasks work with Flask app context.
            Ensures database and other Flask extensions are available in tasks.
            """
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)
        
        celery.Task = ContextTask
    
    return celery


# Create Celery instance
# This will be properly configured when Flask app is created
celery_app = make_celery()

# Import tasks to ensure they are registered with Celery
# This must be done after celery_app is initialized to avoid circular imports
import tuned.tasks.email
import tuned.tasks.order_tasks
