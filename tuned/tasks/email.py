from tuned.celery_app import celery_app
from typing import Any, List, Dict

@celery_app.task(name="tuned.utils.email.send_email_task")
def send_email_task(to: str | List[str], subject: str, template: str, context: Dict[str, Any]) -> None:
    """Celery task for sending emails."""
    from tuned.utils.email import send_email
    from tuned import create_app

    app = create_app()
    with app.app_context():
        send_email(to, subject, template, **context)

@celery_app.task(name="tuned.tasks.email.send_welcome_task")
def send_welcome_task(user_id):
    """Celery task for sending welcome email."""
    from tuned import create_app
    from tuned.models.user import User
    from tuned.services.email_service import send_welcome_email
    
    app = create_app()
    with app.app_context():
        user = User.query.get(user_id)
        if user:
            send_welcome_email(user)