# Client Blueprint Implementation Plan - Part 2

> **Continuation of IMPLEMENTATION_PLAN.md**

---

## 6. Payment Routes

### `GET /client/payments`

**Purpose:** List all payments for the authenticated client

```python
# File: client/routes/payment/list.py

from tuned.client.schemas.payment_schemas import PaymentFilterSchema

@client_bp.route('/payments', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=60, window=60)
def get_payments():
    """
    Get paginated list of payments for authenticated client.

    Query Parameters:
        - page, per_page, status, method, order_id, sort_by, sort_order
    """
    current_user_id = get_jwt_identity()

    schema = PaymentFilterSchema()
    try:
        params = schema.load(request.args)
    except ValidationError as e:
        return error_response('Invalid parameters', errors=e.messages, status=400)

    query = Payment.query.filter_by(user_id=current_user_id)

    # Apply filters
    if params.get('status'):
        query = query.filter_by(status=PaymentStatus(params['status']))
    if params.get('method'):
        query = query.filter_by(method=PaymentMethod(params['method']))
    if params.get('order_id'):
        query = query.filter_by(order_id=params['order_id'])

    # Sort
    sort_field = getattr(Payment, params['sort_by'])
    if params['sort_order'] == 'desc':
        sort_field = sort_field.desc()
    query = query.order_by(sort_field)

    pagination = query.paginate(page=params['page'], per_page=params['per_page'], error_out=False)

    payments = [{
        'id': p.id,
        'payment_id': p.payment_id,
        'order': {
            'id': p.order.id,
            'order_number': p.order.order_number,
            'title': p.order.title
        } if p.order else None,
        'amount': p.amount,
        'currency': p.currency.value,
        'status': p.status.value,
        'method': p.method.value if p.method else None,
        'processor_id': p.processor_id,
        'created_at': p.created_at.isoformat(),
        'paid_at': p.paid_at.isoformat() if p.paid_at else None
    } for p in pagination.items]

    return paginated_response(
        items=payments,
        page=pagination.page,
        per_page=pagination.per_page,
        total=pagination.total
    )
```

### `GET /client/payments/<int:payment_id>/invoice`

**Purpose:** View invoice details

```python
# File: client/routes/payment/invoice.py

@client_bp.route('/payments/<int:payment_id>/invoice', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=100, window=3600)
def get_invoice(payment_id):
    """Get invoice details for a payment"""
    current_user_id = get_jwt_identity()

    payment = Payment.query.filter_by(
        id=payment_id,
        user_id=current_user_id
    ).first()

    if not payment:
        return not_found_response('Payment not found')

    if not payment.invoice:
        return error_response('Invoice not available', status=404)

    invoice = payment.invoice

    return success_response({
        'invoice_number': invoice.invoice_number,
        'issue_date': invoice.created_at.isoformat(),
        'due_date': invoice.due_date.isoformat(),
        'paid': invoice.paid,
        'paid_at': invoice.paid_at.isoformat() if invoice.paid_at else None,
        'order': {
            'order_number': payment.order.order_number,
            'title': payment.order.title,
            'service': payment.order.service.name
        },
        'client': {
            'name': payment.user.get_name(),
            'email': payment.user.email
        },
        'items': [{
            'description': f'{payment.order.service.name} - {payment.order.page_count} pages',
            'quantity': payment.order.page_count,
            'unit_price': invoice.subtotal / payment.order.page_count if payment.order.page_count > 0 else 0,
            'total': invoice.subtotal
        }],
        'subtotal': invoice.subtotal,
        'discount': invoice.discount,
        'tax': invoice.tax,
        'total': invoice.total
    })
```

### `GET /client/payments/<int:payment_id>/invoice/download`

**Purpose:** Download invoice as PDF

```python
@client_bp.route('/payments/<int:payment_id>/invoice/download', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=50, window=3600)
def download_invoice(payment_id):
    """Generate and download invoice PDF"""
    current_user_id = get_jwt_identity()

    payment = Payment.query.filter_by(id=payment_id, user_id=current_user_id).first()

    if not payment or not payment.invoice:
        return not_found_response('Invoice not found')

    # Generate PDF
    from tuned.utils.pdf_generator import generate_invoice_pdf
    pdf_path = generate_invoice_pdf(payment.invoice)

    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f'invoice_{payment.invoice.invoice_number}.pdf'
    )
```

---

## 7. Settings Routes

### `GET /client/settings/profile`

```python
# File: client/routes/settings/profile.py

@client_bp.route('/settings/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile information"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return not_found_response('User not found')

    return success_response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone': user.phone,
        'gender': user.gender.value if user.gender else None,
        'profile_pic': user.profile_pic,
        'reward_points': user.reward_points,
        'created_at': user.created_at.isoformat()
    })
```

### `PUT /client/settings/profile`

```python
from tuned.client.schemas.settings.profile_schema import UpdateProfileSchema

@client_bp.route('/settings/profile', methods=['PUT'])
@jwt_required()
@rate_limit(max_requests=10, window=3600)
@log_activity('profile_updated', 'User')
def update_profile():
    """Update user profile"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return not_found_response('User not found')

    schema = UpdateProfileSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        return error_response('Validation failed', errors=e.messages, status=422)

    # Update fields
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    if 'phone' in data:
        user.phone = data['phone']
    if 'gender' in data:
        user.gender = GenderEnum(data['gender'])

    db.session.commit()

    return success_response({
        'message': 'Profile updated successfully',
        'user': {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'gender': user.gender.value if user.gender else None
        }
    })
```

### `POST /client/settings/newsletter/subscribe`

```python
# File: client/routes/settings/newsletter.py

@client_bp.route('/settings/newsletter/subscribe', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=5, window=3600)
def subscribe_newsletter():
    """Subscribe to newsletter"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    # Check if already subscribed
    existing = NewsletterSubscriber.query.filter_by(email=user.email).first()

    if existing and existing.is_subscribed:
        return error_response('Already subscribed to newsletter', status=400)

    if existing:
        existing.is_subscribed = True
        existing.subscribed_at = datetime.now(timezone.utc)
    else:
        subscriber = NewsletterSubscriber(
            email=user.email,
            name=user.get_name(),
            is_subscribed=True
        )
        db.session.add(subscriber)

    db.session.commit()

    # Send confirmation email
    from tuned.services.email_service import send_newsletter_subscription_email
    send_newsletter_subscription_email(user)

    return success_response({'message': 'Successfully subscribed to newsletter'})
```

### `POST /client/settings/newsletter/unsubscribe`

```python
@client_bp.route('/settings/newsletter/unsubscribe', methods=['POST'])
@jwt_required()
def unsubscribe_newsletter():
    """Unsubscribe from newsletter"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    subscriber = NewsletterSubscriber.query.filter_by(email=user.email).first()

    if not subscriber or not subscriber.is_subscribed:
        return error_response('Not subscribed to newsletter', status=400)

    subscriber.is_subscribed = False
    subscriber.unsubscribed_at = datetime.now(timezone.utc)
    db.session.commit()

    return success_response({'message': 'Successfully unsubscribed from newsletter'})
```

---

## 8. Referral Routes

### `GET /client/referrals`

```python
# File: client/routes/referrals.py

@client_bp.route('/referrals', methods=['GET'])
@jwt_required()
def get_referrals():
    """Get user's referral information"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    # Get referrals made by this user
    referrals_made = Referral.query.filter_by(referrer_id=current_user_id).all()

    # Calculate earnings
    total_earnings = sum(r.commission for r in referrals_made if r.status == ReferralStatus.COMPLETED)

    return success_response({
        'referral_code': user.referral_code,
        'reward_points': user.reward_points,
        'total_referrals': len(referrals_made),
        'active_referrals': len([r for r in referrals_made if r.status == ReferralStatus.ACTIVE]),
        'total_earnings': total_earnings,
        'referrals': [{
            'id': r.id,
            'referred_user': {
                'name': r.referred_user.get_name() if r.referred_user else 'Unknown'
            },
            'status': r.status.value,
            'commission': r.commission,
            'created_at': r.created_at.isoformat()
        } for r in referrals_made]
    })
```

### `POST /client/referrals/redeem`

```python
from tuned.client.schemas.referral_schemas import RedeemRewardSchema

@client_bp.route('/referrals/redeem', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=5, window=86400)
@log_activity('reward_points_redeemed', 'User')
def redeem_reward_points():
    """Redeem reward points for discount on an order"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    schema = RedeemRewardSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        return error_response('Validation failed', errors=e.messages, status=422)

    # Check if user has enough points
    if user.reward_points < data['points']:
        return error_response(f'Insufficient reward points. You have {user.reward_points} points', status=400)

    # Verify order exists and belongs to user
    order = Order.query.filter_by(id=data['order_id'], client_id=current_user_id).first()
    if not order:
        return not_found_response('Order not found')

    # Check if order is in valid state
    if order.paid:
        return error_response('Cannot apply reward points to paid order', status=400)

    # Calculate discount (e.g., 100 points = $1)
    discount_amount = data['points'] / 100

    # Apply discount to order
    order.total_price = max(0, order.total_price - discount_amount)
    user.reward_points -= data['points']

    # Update invoice
    if order.invoice:
        order.invoice.discount += discount_amount
        order.invoice.total = order.total_price

    db.session.commit()

    return success_response({
        'message': f'Successfully redeemed {data["points"]} points',
        'discount_applied': discount_amount,
        'new_order_total': order.total_price,
        'remaining_points': user.reward_points
    })
```

---

## 9. Email Templates (MJML)

All email templates should reside in `backend/tuned/templates/emails/client/orders/`

### Design Specifications

- **Primary Color:** `#4ade80` (green)
- **Secondary Color:** `rgba(48, 54, 87)`
- **Footer Background:** `#1f2937` (dark gray)
- **Body Background:** `#ffffff` (white)
- **Font:** Arial, Helvetica, sans-serif

### Template 1: Order Created (Client)

**File:** `client/orders/order_created_client.html`

**Variables:**

- `{{ recipient_name }}`
- `{{ order_number }}`
- `{{ order_title }}`
- `{{ total_price }}`
- `{{ due_date }}`
- `{{ payment_url }}`
- `{{ order_url }}`
- `{{ support_email }}`
- `{{ current_year }}`

**Structure:**

```html
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Order Created</title>
  </head>
  <body
    style="margin: 0; padding: 0; font-family: Arial, Helvetica, sans-serif; background-color: #f3f4f6;"
  >
    <table
      role="presentation"
      width="100%"
      cellpadding="0"
      cellspacing="0"
      style="background-color: #f3f4f6; padding: 40px 0;"
    >
      <tr>
        <td align="center">
          <table
            role="presentation"
            width="600"
            cellpadding="0"
            cellspacing="0"
            style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"
          >
            <!-- Header -->
            <tr>
              <td
                style="background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%); padding: 50px 30px; text-align: center;"
              >
                <h1
                  style="margin: 0 0 10px; color: #ffffff; font-size: 32px; font-weight: 700;"
                >
                  ✅ Order Confirmed!
                </h1>
                <p
                  style="margin: 0; color: #ffffff; font-size: 16px; opacity: 0.95;"
                >
                  Order #{{ order_number }}
                </p>
              </td>
            </tr>

            <!-- Content -->
            <tr>
              <td style="padding: 50px 40px;">
                <p
                  style="margin: 0 0 25px; color: #374151; font-size: 16px; line-height: 1.6;"
                >
                  Hi {{ recipient_name }},
                </p>

                <p
                  style="margin: 0 0 25px; color: #374151; font-size: 16px; line-height: 1.6;"
                >
                  Your order has been created successfully! To proceed with your
                  project, please complete the payment within the next 30
                  minutes.
                </p>

                <!-- Order Details -->
                <table
                  role="presentation"
                  width="100%"
                  cellpadding="0"
                  cellspacing="0"
                  style="background-color: #f9fafb; border-radius: 6px; padding: 20px; margin: 30px 0;"
                >
                  <tr>
                    <td>
                      <h3
                        style="margin: 0 0 15px; color: #1f2937; font-size: 18px; font-weight: 600;"
                      >
                        Order Details
                      </h3>

                      <table width="100%" cellpadding="8" cellspacing="0">
                        <tr>
                          <td style="color: #6b7280; font-size: 14px;">
                            Order Number:
                          </td>
                          <td
                            style="color: #1f2937; font-weight: 600; font-size: 14px; text-align: right;"
                          >
                            {{ order_number }}
                          </td>
                        </tr>
                        <tr>
                          <td style="color: #6b7280; font-size: 14px;">
                            Title:
                          </td>
                          <td
                            style="color: #1f2937; font-weight: 600; font-size: 14px; text-align: right;"
                          >
                            {{ order_title }}
                          </td>
                        </tr>
                        <tr>
                          <td style="color: #6b7280; font-size: 14px;">
                            Total Amount:
                          </td>
                          <td
                            style="color: #4ade80; font-weight: 700; font-size: 16px; text-align: right;"
                          >
                            ${{ total_price }}
                          </td>
                        </tr>
                        <tr>
                          <td style="color: #6b7280; font-size: 14px;">
                            Due Date:
                          </td>
                          <td
                            style="color: #1f2937; font-weight: 600; font-size: 14px; text-align: right;"
                          >
                            {{ due_date }}
                          </td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                </table>

                <!-- CTA Buttons -->
                <table
                  role="presentation"
                  cellpadding="0"
                  cellspacing="0"
                  style="margin: 35px auto 0; width: 100%;"
                >
                  <tr>
                    <td style="text-align: center; padding-bottom: 15px;">
                      <table
                        role="presentation"
                        cellpadding="0"
                        cellspacing="0"
                        style="margin: 0 auto;"
                      >
                        <tr>
                          <td
                            style="border-radius: 6px; background-color: #4ade80;"
                          >
                            <a
                              href="{{ payment_url }}"
                              target="_blank"
                              style="display: inline-block; padding: 16px 48px; color: #ffffff; text-decoration: none; font-size: 16px; font-weight: 600;"
                            >
                              Complete Payment →
                            </a>
                          </td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                  <tr>
                    <td style="text-align: center;">
                      <a
                        href="{{ order_url }}"
                        target="_blank"
                        style="color: #4ade80; text-decoration: none; font-size: 14px;"
                      >
                        View Order Details
                      </a>
                    </td>
                  </tr>
                </table>

                <!-- Important Notice -->
                <table
                  role="presentation"
                  width="100%"
                  cellpadding="0"
                  cellspacing="0"
                  style="margin: 30px 0;"
                >
                  <tr>
                    <td
                      style="border-left: 4px solid #fbbf24; background-color: #fef3c7; padding: 15px; border-radius: 4px;"
                    >
                      <p style="margin: 0; color: #92400e; font-size: 14px;">
                        <strong>⚠️ Important:</strong> Please complete payment
                        within 30 minutes to secure your order. You will receive
                        a payment reminder email if payment is not completed.
                      </p>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>

            <!-- Divider -->
            <tr>
              <td style="padding: 0 40px;">
                <hr
                  style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;"
                />
              </td>
            </tr>

            <!-- Support -->
            <tr>
              <td style="padding: 0 40px 50px;">
                <p style="margin: 0 0 15px; color: #374151; font-size: 16px;">
                  <strong>Need Help?</strong>
                </p>
                <p
                  style="margin: 0; color: #6b7280; font-size: 14px; line-height: 1.6;"
                >
                  If you have any questions, contact us at
                  <a
                    href="mailto:{{ support_email }}"
                    style="color: #4ade80; text-decoration: none;"
                  >
                    {{ support_email }}
                  </a>
                </p>
              </td>
            </tr>

            <!-- Footer -->
            <tr>
              <td
                style="background-color: #1f2937; padding: 30px 40px; text-align: center;"
              >
                <p style="margin: 0 0 10px; color: #9ca3af; font-size: 14px;">
                  Questions? Email us at
                  <a
                    href="mailto:{{ support_email }}"
                    style="color: #4ade80; text-decoration: none;"
                  >
                    {{ support_email }}
                  </a>
                </p>
                <p style="margin: 0; color: #6b7280; font-size: 12px;">
                  © {{ current_year }} Tuned Essays. All rights reserved.
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
```

### Template 2: Order Created (Admin Notification)

**File:** `admin/orders/order_created_admin.html`

Similar structure but with admin-specific content:

- Client name and email
- Order details
- Link to admin order management
- Assignee suggestions

### Template 3: Payment Reminder

**File:** `client/orders/payment_reminder.html`

**Trigger:** 30 minutes after order creation if payment not completed

**Content:**

- Reminder that payment is pending
- Order details
- Direct payment link
- Countdown/urgency messaging

### Template 4: Payment Complete

**File:** `client/orders/payment_complete_client.html`

**Variables:**

- Payment confirmation details
- Invoice attached/linked
- Next steps (order now being processed)
- Estimated completion date

### Template 5: Files Uploaded

**File:** `admin/orders/files_uploaded_admin.html`

**Trigger:** When client uploads files to order

**Content:**

- Notification that client uploaded files
- File count and list
- Link to view files in admin panel

### Template 6: Order Completed

**File:** `client/orders/order_completed_client.html`

**Trigger:** When admin marks order as delivered

**Content:**

- Delivery notification
- Download links for delivered files
- Review/feedback request
- Revision policy information

### Template 7: Revision Requested

**Files:**

- `admin/orders/revision_requested_admin.html` (to admin)
- `client/orders/revision_requested_client.html` (confirmation to client)

---

## 10. Celery Tasks

### File: `tuned/tasks/order_tasks.py`

```python
from tuned.celery_app import celery
from tuned.models.order import Order
from tuned.models.user import User
from tuned.extensions import db
from tuned.services.email_service import send_payment_reminder_email
from tuned.services.notification_service import create_notification
from tuned.models.enums import NotificationType, OrderStatus
import logging

logger = logging.getLogger(__name__)

@celery.task(name='tasks.send_payment_reminder')
def send_payment_reminder(order_id):
    """
    Send payment reminder 30 minutes after order creation if not paid.
    """
    try:
        order = Order.query.get(order_id)

        if not order:
            logger.warning(f'Order {order_id} not found for payment reminder')
            return

        # Only send if order is still pending and not paid
        if order.paid or order.status != OrderStatus.PENDING:
            logger.info(f'Order {order_id} already paid or status changed, skipping reminder')
            return

        user = User.query.get(order.client_id)
        if not user:
            logger.error(f'User {order.client_id} not found for order {order_id}')
            return

        # Send email
        send_payment_reminder_email(user, order)

        # Create notification
        create_notification(
            user_id=order.client_id,
            title='Payment Reminder',
            message=f'Reminder: Please complete payment for order #{order.order_number}',
            type=NotificationType.WARNING,
            link=f'/orders/{order.id}/payment'
        )

        logger.info(f'Payment reminder sent for order {order_id}')

    except Exception as e:
        logger.error(f'Error sending payment reminder for order {order_id}: {str(e)}')
        raise


@celery.task(name='tasks.check_overdue_orders')
def check_overdue_orders():
    """
    Periodic task to check and mark overdue orders.
    Run every hour via Celery Beat.
    """
    from datetime import datetime, timezone

    try:
        now = datetime.now(timezone.utc)

        # Find orders that are past due date and still active
        overdue_orders = Order.query.filter(
            Order.due_date < now,
            Order.status.in_([OrderStatus.ACTIVE, OrderStatus.PENDING]),
            Order.is_active == True
        ).all()

        for order in overdue_orders:
            # Update status
            order.status = OrderStatus.OVERDUE

            # Notify client
            create_notification(
                user_id=order.client_id,
                title=f'Order Overdue - #{order.order_number}',
                message=f'Your order "{order.title}" is now overdue',
                type=NotificationType.ERROR,
                link=f'/orders/{order.id}'
            )

            # Notify admins
            admins = User.query.filter_by(is_admin=True, is_active=True).all()
            for admin in admins:
                create_notification(
                    user_id=admin.id,
                    title=f'Order Overdue - #{order.order_number}',
                    message=f'Order "{order.title}" is now overdue',
                    type=NotificationType.ERROR,
                    link=f'/admin/orders/{order.id}'
                )

        db.session.commit()
        logger.info(f'Marked {len(overdue_orders)} orders as overdue')

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error checking overdue orders: {str(e)}')
        raise


@celery.task(name='tasks.send_due_date_reminders')
def send_due_date_reminders():
    """
    Send reminders for orders due in next 24 hours.
    Run daily via Celery Beat.
    """
    from datetime import datetime, timedelta, timezone

    try:
        now = datetime.now(timezone.utc)
        tomorrow = now + timedelta(hours=24)

        # Find orders due in next 24 hours
        upcoming_orders = Order.query.filter(
            Order.due_date.between(now, tomorrow),
            Order.status == OrderStatus.ACTIVE,
            Order.is_active == True
        ).all()

        for order in upcoming_orders:
            # Notify client
            create_notification(
                user_id=order.client_id,
                title=f'Order Due Soon - #{order.order_number}',
                message=f'Your order "{order.title}" is due within 24 hours',
                type=NotificationType.WARNING,
                link=f'/orders/{order.id}'
            )

        logger.info(f'Sent due date reminders for {len(upcoming_orders)} orders')

    except Exception as e:
        logger.error(f'Error sending due date reminders: {str(e)}')
        raise
```

### Celery Beat Schedule

Add to `tuned/celery_app.py`:

```python
from celery.schedules import crontab

celery.conf.beat_schedule = {
    'check-overdue-orders': {
        'task': 'tasks.check_overdue_orders',
        'schedule': crontab(minute=0),  # Every hour
    },
    'send-due-date-reminders': {
        'task': 'tasks.send_due_date_reminders',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
    },
}
```

---

## 11. Email Service Functions

### File: `tuned/services/email_service.py` (additions)

```python
def send_order_created_email_client(user, order):
    """Send order creation confirmation to client"""
    from flask import current_app

    subject = f"Order Confirmed - #{order.order_number}"
    template = 'emails/client/orders/order_created_client.html'

    context = {
        'recipient_name': user.get_name(),
        'order_number': order.order_number,
        'order_title': order.title,
        'total_price': f'{order.total_price:.2f}',
        'due_date': order.due_date.strftime('%B %d, %Y at %I:%M %p'),
        'payment_url': f"{current_app.config.get('FRONTEND_URL')}/orders/{order.id}/payment",
        'order_url': f"{current_app.config.get('FRONTEND_URL')}/orders/{order.id}",
        'support_email': current_app.config.get('MAIL_DEFAULT_SENDER'),
        'current_year': datetime.now().year
    }

    send_async_email.delay(
        to=user.email,
        subject=subject,
        template=template,
        context=context
    )

def send_order_created_email_admin(order):
    """Send new order notification to admins"""
    from flask import current_app
    from tuned.models.user import User

    admins = User.query.filter_by(is_admin=True, is_active=True).all()

    subject = f"New Order Received - #{order.order_number}"
    template = 'emails/admin/orders/order_created_admin.html'

    for admin in admins:
        context = {
            'admin_name': admin.get_name(),
            'order_number': order.order_number,
            'order_title': order.title,
            'client_name': order.client.get_name(),
            'client_email': order.client.email,
            'total_price': f'{order.total_price:.2f}',
            'service_name': order.service.name,
            'due_date': order.due_date.strftime('%B %d, %Y at %I:%M %p'),
            'admin_order_url': f"{current_app.config.get('FRONTEND_URL')}/admin/orders/{order.id}",
            'current_year': datetime.now().year
        }

        send_async_email.delay(
            to=admin.email,
            subject=subject,
            template=template,
            context=context
        )

def send_payment_reminder_email(user, order):
    """Send payment reminder email"""
    from flask import current_app

    subject = f"Payment Reminder - Order #{order.order_number}"
    template = 'emails/client/orders/payment_reminder.html'

    context = {
        'recipient_name': user.get_name(),
        'order_number': order.order_number,
        'order_title ': order.title,
        'total_price': f'{order.total_price:.2f}',
        'payment_url': f"{current_app.config.get('FRONTEND_URL')}/orders/{order.id}/payment",
        'support_email': current_app.config.get('MAIL_DEFAULT_SENDER'),
        'current_year': datetime.now().year
    }

    send_async_email.delay(
        to=user.email,
        subject=subject,
        template=template,
        context=context
    )

# Add similar functions for:
# - send_payment_complete_email_client()
# - send_files_uploaded_email_admin()
# - send_order_completed_email_client()
# - send_revision_request_email_admin()
# - send_revision_request_email_client()
# - send_deadline_extension_request_email_admin()
```

---

## 12. Testing Strategy

### Unit Tests

**File:** `tests/test_client_orders.py`

```python
import pytest
from tuned.models.order import Order
from tuned.models.user import User
from tuned.models.service import Service
from tuned.models.enums import OrderStatus

class TestOrderCreation:

    def test_create_order_success(self, client, auth_headers, test_db):
        """Test successful order creation"""
        data = {
            'service_id': 1,
            'academic_level_id': 1,
            'deadline_id': 1,
            'title': 'Test Essay',
            'description': 'This is a comprehensive test description for the essay',
            'word_count': 1000,
            'page_count': 4
        }

        response = client.post('/client/orders/create',
                             json=data,
                             headers=auth_headers)

        assert response.status_code == 201
        assert 'order' in response.json['data']
        assert response.json['data']['order']['title'] == 'Test Essay'

    def test_create_order_validation_error(self, client, auth_headers):
        """Test order creation with invalid data"""
        data = {
            'service_id': 1,
            'title': 'Short',  # Too short
            'word_count': -100  # Negative
        }

        response = client.post('/client/orders/create',
                             json=data,
                             headers=auth_headers)

        assert response.status_code == 422
        assert 'errors' in response.json

    def test_create_order_unauthorized(self, client):
        """Test order creation without authentication"""
        response = client.post('/client/orders/create', json={})
        assert response.status_code == 401
```

### Integration Tests

**File:** `tests/integration/test_order_flow.py`

```python
class TestOrderWorkflow:

    def test_complete_order_flow(self, client, auth_headers, test_db):
        """Test complete order lifecycle"""

        # 1. Create order
        order_data = {...}
        create_response = client.post('/client/orders/create',
                                     json=order_data,
                                     headers=auth_headers)
        assert create_response.status_code == 201
        order_id = create_response.json['data']['order']['id']

        # 2. Upload files
        files_response = client.post(f'/client/orders/{order_id}/files/upload',
                                    data={'files': [(io.BytesIO(b'test'), 'test.pdf')]},
                                    headers=auth_headers)
        assert files_response.status_code == 201

        # 3. Add comment
        comment_data = {'message': 'Please include references'}
        comment_response = client.post(f'/client/orders/{order_id}/comments',
                                      json=comment_data,
                                      headers=auth_headers)
        assert comment_response.status_code == 201

        # 4. Request revision (after delivery - setup needed)
        # ... etc
```

### Email Template Tests

**File:** `tests/test_email_templates.py`

```python
def test_order_created_email_renders(app):
    """Test that order created email template renders correctly"""
    with app.app_context():
        from flask import render_template

        context = {
            'recipient_name': 'John Doe',
            'order_number': 'ORD-202602-0001',
            'order_title': 'Test Essay',
            'total_price': '50.00',
            # ... other vars
        }

        html = render_template('emails/client/orders/order_created_client.html', **context)

        assert 'John Doe' in html
        assert 'ORD-202602-0001' in html
        assert '$50.00' in html
```

---

## 13. Implementation Phases

### Phase 1: Foundation (Week 1)

- [x] Create validation schemas for all routes
- [x] Set up base route structure
- [x] Implement authentication decorators
- [ ] Create database migrations if needed

### Phase 2: Order Routes (Week 1-2)

- [ ] Implement order creation endpoint
- [ ] Implement order listing/filtering
- [ ] Implement order detail view
- [ ] Add file upload/download functionality
- [ ] Implement comments system
- [ ] Add support tickets
- [ ] Implement deadline extension
- [ ] Implement revision requests

### Phase 3: Payment & Settings (Week 2)

- [ ] Implement payment listing
- [ ] Implement invoice view/download
- [ ] Implement profile management
- [ ] Implement newsletter subscription

### Phase 4: Referrals (Week 2)

- [ ] Implement referral tracking
- [ ] Implement reward redemption

### Phase 5: Email Templates (Week 3)

- [ ] Create all MJML templates
- [ ] Implement email service functions
- [ ] Test email rendering

### Phase 6: Notifications & Real-time (Week 3)

- [ ] Integrate notification service
- [ ] Implement SocketIO events
- [ ] Test real-time updates

### Phase 7: Celery Tasks (Week 3-4)

- [ ] Implement payment reminder task
- [ ] Implement overdue checker
- [ ] Implement due date reminders
- [ ] Configure Celery Beat

### Phase 8: Testing & Documentation (Week 4)

- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Test all email templates
- [ ] Create API documentation
- [ ] Perform security audit

---

## 14. Security Checklist

- [ ] All routes protected with `@jwt_required()`
- [ ] Rate limiting on all endpoints
- [ ] Input validation via Marshmallow schemas
- [ ] SQL injection prevention (using SQLAlchemy ORM)
- [ ] File upload validation (type, size)
- [ ] Activity logging for sensitive operations
- [ ] CORS properly configured
- [ ] Proper error handling (don't leak sensitive info)
- [ ] API key protection for internal endpoints

---

## 15. Next.js Integration

Each API endpoint should have a corresponding TypeScript client:

**Example:** `frontend/lib/api/orders.ts`

```typescript
export const createOrder = async (
  data: CreateOrderData,
): Promise<OrderResponse> => {
  const response = await fetch(`${API_BASE_URL}/client/orders/create`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${getAccessToken()}`,
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error("Failed to create order");
  }

  return response.json();
};
```

---

**END OF IMPLEMENTATION PLAN**
