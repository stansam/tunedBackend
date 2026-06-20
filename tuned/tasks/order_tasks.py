from typing import Any
from tuned.celery_app import celery_app as celery

@celery.task  # type: ignore[untyped-decorator]
def send_payment_reminder(order_id: str) -> str:
    try:
        from tuned.models.order import Order
        from tuned.services.email_service import send_payment_reminder_email
        from tuned.extensions import db
        
        order = db.session.query(Order).get(order_id)
        if order and not order.paid:
            send_payment_reminder_email(order)
            return f'Payment reminder sent for order {order.order_number}'
        return 'Order already paid or not found'
    except Exception as e:
        return f'Error sending payment reminder: {str(e)}'

@celery.task  # type: ignore[untyped-decorator]
def schedule_draft_reminder(order_id: str) -> str:
    try:
        from tuned.models.order import Order
        from tuned.models.enums import OrderStatus, NotificationType
        from tuned.tasks.notifications import create_in_app_notification
        from tuned.extensions import db
        import logging
        
        logger = logging.getLogger(__name__)
        order = db.session.query(Order).get(order_id)
        if order and order.status == OrderStatus.DRAFT:
            # Send system notification
            create_in_app_notification.delay(
                user_id=order.client_id,
                title="Draft Order Reminder",
                message="You have a saved draft order. Complete it to start your project!",
                notification_type=NotificationType.INFO.value.upper(),
            )
            # TODO: add email service logic here
            return f'Draft reminder sent for order {order.id}'
        return 'Order is no longer a draft or not found'
    except Exception as e:
        return f'Error sending draft reminder: {str(e)}'
