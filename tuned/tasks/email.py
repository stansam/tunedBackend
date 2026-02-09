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