from __future__ import annotations

from celery import Task
from celery.utils.log import get_task_logger
from tuned.celery_app import celery_app

logger = get_task_logger(__name__)

@celery_app.task(
    name="tuned.tasks.payment_tasks.generate_monthly_invoices",
    bind=True,
    queue="notifications",
    acks_late=True,
)
def generate_monthly_invoices(self: Task) -> None:
    """
    Generates monthly invoice summaries for all active orders.
    TODO: Implement full invoice generation logic when billing module is complete.
    """
    logger.info("[PaymentTasks] generate_monthly_invoices triggered — not yet implemented")
