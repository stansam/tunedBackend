"""
Celery tasks for order processing.

This module contains async tasks for order-related operations.
"""

from tuned.celery_app import celery_app as celery


@celery.task
def send_payment_reminder(order_id):
    """
    Send payment reminder email for unpaid order.
    
    Args:
        order_id: ID of the order
    """
    try:
        from tuned.models.order import Order
        from tuned.services.email_service import send_payment_reminder_email
        
        order = Order.query.get(order_id)
        if order and not order.paid:
            send_payment_reminder_email(order)
            return f'Payment reminder sent for order {order.order_number}'
        return 'Order already paid or not found'
    except Exception as e:
        return f'Error sending payment reminder: {str(e)}'
