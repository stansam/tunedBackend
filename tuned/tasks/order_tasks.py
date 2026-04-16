from tuned.celery_app import celery_app as celery


@celery.task
def send_payment_reminder(order_id):
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
