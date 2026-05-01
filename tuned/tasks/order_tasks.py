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
