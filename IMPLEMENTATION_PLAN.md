# Client Blueprint Implementation Plan

> **Document Version:** 1.0  
> **Date:** 2026-02-01  
> **Status:** Ready for Implementation

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture & Patterns](#architecture--patterns)
3. [Validation Schemas](#validation-schemas)
4. [API Routes Specification](#api-routes-specification)
5. [Email Templates](#email-templates)
6. [Notifications & Real-time](#notifications--real-time)
7. [Celery Tasks](#celery-tasks)
8. [Testing Strategy](#testing-strategy)
9. [Implementation Phases](#implementation-phases)

---

## Overview

### Objective

Implement a production-ready client blueprint for the academic writing platform, providing secure, maintainable APIs for:

- Order management (create, view, comments, files, tickets, revisions, deadline extensions)
- Payment management (view, invoice download)
- Profile & settings management
- Referral & rewards tracking

### Design Principles

1. **Security First**: JWT authentication, input validation, rate limiting
2. **Consistency**: Follow existing patterns in utils, services, models
3. **Separation of Concerns**: Routes → Schemas → Services → Models
4. **Audit Trail**: Log all critical actions via ActivityLog
5. **Real-time**: SocketIO for notifications and updates
6. **Email Communication**: MJML-based templates for professional emails

---

## Architecture & Patterns

### Request Flow

```
Client Request
    ↓
JWT Authentication (@jwt_required())
    ↓
Rate Limiting (@rate_limit)
    ↓
Request Validation (Marshmallow schema)
    ↓
Business Logic (Service layer)
    ↓
Database Operations (SQLAlchemy models)
    ↓
Activity Logging (ActivityLog.log())
    ↓
Notification/Email (if applicable)
    ↓
Standardized Response (success_response/error_response)
```

### File Organization

```
client/
├── __init__.py (Blueprint registration)
├── schemas/
│   ├── __init__.py
│   ├── order_schemas.py (NEW)
│   ├── payment_schemas.py (NEW)
│   ├── settings/ (existing, verify completeness)
│   └── referral_schemas.py (NEW)
│
├── routes/
│   ├── orders/
│   │   ├── create.py ✅
│   │   ├── get.py ✅
│   │   └── activities/
│   │       ├── comments/ ✅
│   │       ├── files/ ✅
│   │       ├── tickets/ ✅
│   │       ├── extend_deadline.py ✅
│   │       └── request_revision.py ✅
│   │
│   ├── payment/ ✅
│   ├── settings/ (verify)
│   └── referrals.py ✅
│
└── services/
    ├── __init__.py
    ├── order_service.py (NEW)
    └── payment_service.py (NEW)
```

---

## Validation Schemas

All schemas use **Marshmallow** with Flask integration.

### 1. Order Schemas (`client/schemas/order_schemas.py`)

```python
from marshmallow import Schema, fields, validates, ValidationError, validate
from tuned.models.enums import OrderStatus

class CreateOrderSchema(Schema):
    """Validation for order creation"""
    service_id = fields.Integer(required=True)
    academic_level_id = fields.Integer(required=True)
    deadline_id = fields.Integer(required=True)
    title = fields.String(required=True, validate=validate.Length(min=5, max=255))
    description = fields.Text(required=True, validate=validate.Length(min=20))
    word_count = fields.Integer(required=True, validate=validate.Range(min=250, max=50000))
    page_count = fields.Float(required=True, validate=validate.Range(min=1, max=200))
    format_style = fields.String(allow_none=True, validate=validate.OneOf(['APA', 'MLA', 'Chicago', 'Harvard']))
    report_type = fields.String(allow_none=True)
    discount_code = fields.String(allow_none=True)

class OrderFilterSchema(Schema):
    """Query parameters for listing orders"""
    page = fields.Integer(missing=1, validate=validate.Range(min=1))
    per_page = fields.Integer(missing=10, validate=validate.Range(min=1, max=100))
    status = fields.String(allow_none=True, validate=validate.OneOf([s.value for s in OrderStatus]))
    search = fields.String(allow_none=True)
    sort_by = fields.String(missing='created_at', validate=validate.OneOf(['created_at', 'due_date', 'total_price']))
    sort_order = fields.String(missing='desc', validate=validate.OneOf(['asc', 'desc']))

class OrderCommentSchema(Schema):
    """Validation for order comments"""
    message = fields.String(required=True, validate=validate.Length(min=1, max=5000))

class ExtendDeadlineSchema(Schema):
    """Validation for deadline extension requests"""
    requested_hours = fields.Integer(required=True, validate=validate.Range(min=12, max=720))
    reason = fields.String(required=True, validate=validate.Length(min=20, max=500))

class RequestRevisionSchema(Schema):
    """Validation for revision requests"""
    delivery_id = fields.Integer(required=True)
    revision_notes = fields.String(required=True, validate=validate.Length(min=20, max=2000))

class SupportTicketSchema(Schema):
    """Validation for support tickets"""
    subject = fields.String(required=True, validate=validate.Length(min=5, max=255))
    message = fields.String(required=True, validate=validate.Length(min=20, max=5000))
```

### 2. Payment Schemas (`client/schemas/payment_schemas.py`)

```python
from marshmallow import Schema, fields, validate
from tuned.models.enums import PaymentStatus, PaymentMethod

class PaymentFilterSchema(Schema):
    """Query parameters for listing payments"""
    page = fields.Integer(missing=1, validate=validate.Range(min=1))
    per_page = fields.Integer(missing=10, validate=validate.Range(min=1, max=100))
    status = fields.String(allow_none=True, validate=validate.OneOf([s.value for s in PaymentStatus]))
    method = fields.String(allow_none=True, validate=validate.OneOf([m.value for m in PaymentMethod]))
    order_id = fields.Integer(allow_none=True)
    sort_by = fields.String(missing='created_at')
    sort_order = fields.String(missing='desc', validate=validate.OneOf(['asc', 'desc']))

class ManualPaymentConfirmationSchema(Schema):
    """Validation for manual payment confirmation submission"""
    order_id = fields.Integer(required=True)
    payment_method = fields.String(required=True, validate=validate.OneOf([m.value for m in PaymentMethod]))
    payer_email = fields.Email(required=True)
    amount = fields.Float(required=True, validate=validate.Range(min=0.01))
    transaction_reference = fields.String(allow_none=True, validate=validate.Length(max=255))
```

### 3. Settings Schemas (Verify existing, add if needed)

Path: `client/schemas/settings/`

Expected files:

- `profile_schema.py` - Profile update validation
- `password_schema.py` - Password change validation
- `notification_schema.py` - Notification preferences
- `newsletter_schema.py` - Newsletter subscription toggle

### 4. Referral Schemas (`client/schemas/referral_schemas.py`)

```python
class ReferralSchema(Schema):
    """Validation for referral operations"""
    referral_code = fields.String(validate=validate.Length(equal=10))

class RedeemRewardSchema(Schema):
    """Validation for reward point redemption"""
    points = fields.Integer(required=True, validate=validate.Range(min=100))
    order_id = fields.Integer(required=True)
```

---

## API Routes Specification

### Authentication Decorator Pattern

**All client routes must use:**

```python
from flask_jwt_extended import jwt_required, get_jwt_identity

@client_bp.route('/path', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=60, window=60)  # 60 req/min
def route_handler():
    current_user_id = get_jwt_identity()
    # Implementation
```

---

### 1. Order Routes

#### `POST /client/orders/create`

**Purpose:** Create a new order

```python
# File: client/routes/orders/create.py

from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from tuned.client import client_bp
from tuned.client.schemas.order_schemas import CreateOrderSchema
from tuned.models.order import Order
from tuned.models.user import User
from tuned.models.service import Service, AcademicLevel, Deadline
from tuned.models.payment import Discount
from tuned.utils import success_response, error_response, created_response
from tuned.utils.decorators import rate_limit, log_activity
from tuned.extensions import db
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)

@client_bp.route('/orders/create', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=10, window=3600)  # 10 orders per hour
@log_activity('order_created', 'Order')
def create_order():
    """
    Create a new order for the authenticated client.

    Request Body:
        - service_id: int
        - academic_level_id: int
        - deadline_id: int
        - title: str
        - description: str
        - word_count: int
        - page_count: float
        - format_style: str (optional)
        - report_type: str (optional)
        - discount_code: str (optional)

    Returns:
        201: Order created successfully
        400: Validation error
        404: Service/level/deadline not found
        401: Unauthorized
    """
    current_user_id = get_jwt_identity()

    # Validate request
    schema = CreateOrderSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        return error_response('Validation failed', errors=e.messages, status=422)

    # Verify user exists
    user = User.query.get(current_user_id)
    if not user or not user.is_active:
        return error_response('User not found', status=404)

    # Verify service, level, deadline exist
    service = Service.query.get(data['service_id'])
    academic_level = AcademicLevel.query.get(data['academic_level_id'])
    deadline = Deadline.query.get(data['deadline_id'])

    if not service or not service.is_active:
        return error_response('Service not found', status=404)
    if not academic_level:
        return error_response('Academic level not found', status=404)
    if not deadline:
        return error_response('Deadline not found', status=404)

    # Calculate total price
    from tuned.models.price import PriceRate
    price_rate = PriceRate.query.filter_by(
        pricing_category_id=service.pricing_category_id,
        academic_level_id=data['academic_level_id'],
        deadline_id=data['deadline_id'],
        is_active=True
    ).first()

    if not price_rate:
        return error_response('Pricing not available for this combination', status=400)

    total_price = price_rate.price_per_page * data['page_count']

    # Apply discount if provided
    discount = None
    if data.get('discount_code'):
        discount = Discount.query.filter_by(
            code=data['discount_code'].upper(),
            is_active=True
        ).first()

        if discount:
            # Validate discount
            if discount.valid_from and discount.valid_from > datetime.now(timezone.utc):
                return error_response('Discount code not yet valid', status=400)
            if discount.valid_to and discount.valid_to < datetime.now(timezone.utc):
                return error_response('Discount code expired', status=400)
            if discount.usage_limit and discount.times_used >= discount.usage_limit:
                return error_response('Discount code usage limit reached', status=400)
            if total_price < discount.min_order_value:
                return error_response(f'Minimum order value for this discount is ${discount.min_order_value}', status=400)

            # Calculate discount
            if discount.discount_type.value == 'percentage':
                discount_amount = total_price * (discount.amount / 100)
            else:  # fixed
                discount_amount = discount.amount

            # Apply max discount limit
            if discount.max_discount_value:
                discount_amount = min(discount_amount, discount.max_discount_value)

            total_price -= discount_amount

    # Calculate due date
    due_date = datetime.now(timezone.utc) + timedelta(hours=deadline.hours)

    # Create order
    order = Order(
        client_id=current_user_id,
        service_id=data['service_id'],
        academic_level_id=data['academic_level_id'],
        deadline_id=data['deadline_id'],
        title=data['title'],
        description=data['description'],
        word_count=data['word_count'],
        page_count=data['page_count'],
        format_style=data.get('format_style'),
        report_type=data.get('report_type'),
        total_price=total_price,
        due_date=due_date,
        status=OrderStatus.PENDING,
        paid=False
    )

    try:
        db.session.add(order)

        # Apply discount if applicable
        if discount:
            order.discounts.append(discount)
            discount.times_used += 1

        db.session.commit()

        # Create invoice
        from tuned.models.payment import Invoice
        invoice = Invoice(
            order_id=order.id,
            user_id=current_user_id,
            subtotal=price_rate.price_per_page * data['page_count'],
            discount=discount_amount if discount else 0,
            tax=0,  # Add tax calculation if applicable
            total=total_price,
            due_date=due_date,
            paid=False
        )
        db.session.add(invoice)
        db.session.commit()

        # Send notifications
        from tuned.services.notification_service import create_notification
        from tuned.models.enums import NotificationType

        # Client notification
        create_notification(
            user_id=current_user_id,
            title='Order Created Successfully',
            message=f'Your order "{order.title}" has been created. Please complete payment to proceed.',
            type=NotificationType.SUCCESS,
            link=f'/orders/{order.id}'
        )

        # Admin notification (send to all admins)
        admins = User.query.filter_by(is_admin=True, is_active=True).all()
        for admin in admins:
            create_notification(
                user_id=admin.id,
                title='New Order Received',
                message=f'Client {user.get_name()} created order #{order.order_number}',
                type=NotificationType.INFO,
                link=f'/admin/orders/{order.id}'
            )

        # Send emails
        from tuned.services.email_service import send_order_created_email_client, send_order_created_email_admin
        send_order_created_email_client(user, order)
        send_order_created_email_admin(order)

        # Schedule payment reminder (30 minutes)
        from tuned.tasks.order_tasks import send_payment_reminder
        send_payment_reminder.apply_async(args=[order.id], countdown=1800)  # 30 min

        logger.info(f'Order {order.order_number} created by user {current_user_id}')

        return created_response({
            'order': {
                'id': order.id,
                'order_number': order.order_number,
                'title': order.title,
                'total_price': order.total_price,
                'status': order.status.value,
                'due_date': order.due_date.isoformat(),
                'created_at': order.created_at.isoformat()
            }
        }, 'Order created successfully')

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error creating order: {str(e)}')
        return error_response('Failed to create order', status=500)
```

#### `GET /client/orders`

**Purpose:** List all orders for the authenticated client

```python
# File: client/routes/orders/get.py

@client_bp.route('/orders', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=60, window=60)
def get_orders():
    """
    Get paginated list of orders for authenticated client.

    Query Parameters:
        - page: int (default: 1)
        - per_page: int (default: 10, max: 100)
        - status: str (optional)
        - search: str (optional - searches in title, description, order_number)
        - sort_by: str (default: 'created_at')
        - sort_order: str (default: 'desc')

    Returns:
        200: Paginated orders list
        400: Validation error
    """
    current_user_id = get_jwt_identity()

    # Validate query parameters
    schema = OrderFilterSchema()
    try:
        params = schema.load(request.args)
    except ValidationError as e:
        return error_response('Invalid query parameters', errors=e.messages, status=400)

    # Build query
    query = Order.query.filter_by(client_id=current_user_id, is_active=True)

    # Apply filters
    if params.get('status'):
        query = query.filter_by(status=OrderStatus(params['status']))

    if params.get('search'):
        search_term = f"%{params['search']}%"
        query = query.filter(
            or_(
                Order.title.ilike(search_term),
                Order.description.ilike(search_term),
                Order.order_number.ilike(search_term)
            )
        )

    # Sorting
    sort_field = getattr(Order, params['sort_by'])
    if params['sort_order'] == 'desc':
        sort_field = sort_field.desc()
    query = query.order_by(sort_field)

    # Pagination
    pagination = query.paginate(
        page=params['page'],
        per_page=params['per_page'],
        error_out=False
    )

    # Serialize
    orders = [{
        'id': order.id,
        'order_number': order.order_number,
        'title': order.title,
        'service': order.service.name,
        'total_price': order.total_price,
        'status': order.status.value,
        'status_color': order.status_color,
        'paid': order.paid,
        'due_date': order.due_date.isoformat(),
        'created_at': order.created_at.isoformat(),
        'is_delivered': order.is_delivered,
        'latest_delivery': {
            'id': order.latest_delivery.id,
            'delivered_at': order.latest_delivery.delivered_at.isoformat(),
            'status': order.latest_delivery.delivery_status.value
        } if order.latest_delivery else None
    } for order in pagination.items]

    return paginated_response(
        items=orders,
        page=pagination.page,
        per_page=pagination.per_page,
        total=pagination.total
    )
```

#### `GET /client/orders/<int:order_id>`

**Purpose:** Get single order details

```python
@client_bp.route('/orders/<int:order_id>', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=100, window=60)
def get_order(order_id):
    """Get detailed information about a specific order"""
    current_user_id = get_jwt_identity()

    order = Order.query.filter_by(
        id=order_id,
        client_id=current_user_id,
        is_active=True
    ).first()

    if not order:
        return not_found_response('Order not found')

    # Comprehensive order details
    return success_response({
        'id': order.id,
        'order_number': order.order_number,
        'title': order.title,
        'description': order.description,
        'service': {
            'id': order.service.id,
            'name': order.service.name
        },
        'academic_level': {
            'id': order.academic_level.id,
            'name': order.academic_level.name
        },
        'deadline': {
            'id': order.deadline.id,
            'name': order.deadline.name,
            'hours': order.deadline.hours
        },
        'word_count': order.word_count,
        'page_count': order.page_count,
        'format_style': order.format_style,
        'report_type': order.report_type,
        'total_price': order.total_price,
        'status': order.status.value,
        'status_color': order.status_color,
        'paid': order.paid,
        'due_date': order.due_date.isoformat(),
        'created_at': order.created_at.isoformat(),
        'writer_assigned': order.writer_is_assigned,
        'extension_requested': order.extension_requested,

        # Files
        'files': [{
            'id': f.id,
            'filename': f.filename,
            'uploaded_at': f.uploaded_at.isoformat(),
            'size': f.file_size,
            'is_from_client': f.is_from_client
        } for f in order.files],

        # Deliveries
        'deliveries': [{
            'id': d.id,
            'delivery_status': d.delivery_status.value,
            'delivered_at': d.delivered_at.isoformat(),
            'has_plagiarism_report': d.has_plagiarism_report,
            'files': [{
                'id': df.id,
                'filename': df.filename,
                'file_type': df.file_type.value,
                'file_format': df.file_format,
                'size': df.file_size_mb
            } for df in d.delivery_files]
        } for d in order.deliveries],

        # Comments (recent 10)
        'recent_comments': [{
            'id': c.id,
            'message': c.message,
            'is_admin': c.is_admin,
            'created_at': c.created_at.isoformat(),
            'user_name': c.user.get_name()
        } for c in order.comments[:10]],

        # Invoice
        'invoice': {
            'invoice_number': order.invoice.invoice_number,
            'subtotal': order.invoice.subtotal,
            'discount': order.invoice.discount,
            'tax': order.invoice.tax,
            'total': order.invoice.total,
            'paid': order.invoice.paid
        } if order.invoice else None
    })
```

### 2. Order Activity Routes

#### `GET /client/orders/<int:order_id>/comments`

```python
# File: client/routes/orders/activities/comments/get.py

@client_bp.route('/orders/<int:order_id>/comments', methods=['GET'])
@jwt_required()
def get_order_comments(order_id):
    """Get all comments for an order"""
    current_user_id = get_jwt_identity()

    order = Order.query.filter_by(
        id=order_id,
        client_id=current_user_id,
        is_active=True
    ).first()

    if not order:
        return not_found_response('Order not found')

    comments = [{
        'id': c.id,
        'message': c.message,
        'is_admin': c.is_admin,
        'is_read': c.is_read,
        'created_at': c.created_at.isoformat(),
        'user': {
            'id': c.user.id,
            'name': c.user.get_name(),
            'profile_pic': c.user.profile_pic
        }
    } for c in order.comments]

    # Mark client's unread comments as read
    OrderComment.query.filter_by(
        order_id=order_id,
        is_admin=True,
        is_read=False
    ).update({'is_read': True})
    db.session.commit()

    return success_response(comments)
```

#### `POST /client/orders/<int:order_id>/comments`

```python
# File: client/routes/orders/activities/comments/create.py

@client_bp.route('/orders/<int:order_id>/comments', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=30, window=60)
@log_activity('comment_added', 'OrderComment')
def create_order_comment(order_id):
    """Add a comment to an order"""
    current_user_id = get_jwt_identity()

    # Verify order ownership
    order = Order.query.filter_by(
        id=order_id,
        client_id=current_user_id,
        is_active=True
    ).first()

    if not order:
        return not_found_response('Order not found')

    # Validate
    schema = OrderCommentSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        return error_response('Validation failed', errors=e.messages, status=422)

    # Create comment
    comment = OrderComment(
        order_id=order_id,
        user_id=current_user_id,
        message=data['message'],
        is_admin=False,
        is_read=False
    )

    db.session.add(comment)
    db.session.commit()

    # Notify admin
    admins = User.query.filter_by(is_admin=True, is_active=True).all()
    for admin in admins:
        create_notification(
            user_id=admin.id,
            title=f'New Comment on Order #{order.order_number}',
            message=f'Client added a comment on order {order.title}',
            type=NotificationType.INFO,
            link=f'/admin/orders/{order.id}'
        )

    # Emit socket event
    from tuned.extensions import socketio
    socketio.emit('order:comment_added', {
        'order_id': order.id,
        'comment': {
            'id': comment.id,
            'message': comment.message,
            'user_name': comment.user.get_name(),
            'created_at': comment.created_at.isoformat()
        }
    }, room=f'order_{order.id}')

    return created_response({
        'id': comment.id,
        'message': comment.message,
        'created_at': comment.created_at.isoformat()
    }, 'Comment added successfully')
```

#### Similar implementation for:

- `PUT /client/orders/<int:order_id>/comments/<int:comment_id>` - Edit comment
- `DELETE /client/orders/<int:order_id>/comments/<int:comment_id>` - Delete comment

---

### 3. File Upload/Download Routes

#### `POST /client/orders/<int:order_id>/files/upload`

```python
# File: client/routes/orders/activities/files/upload.py

from werkzeug.utils import secure_filename
import os
from flask import current_app

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'zip', 'rar'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@client_bp.route('/orders/<int:order_id>/files/upload', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=20, window=3600)
@log_activity('file_uploaded', 'OrderFile')
def upload_order_file(order_id):
    """Upload files for an order"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    # Verify order
    order = Order.query.filter_by(
        id=order_id,
        client_id=current_user_id,
        is_active=True
    ).first()

    if not order:
        return not_found_response('Order not found')

    # Check if files in request
    if 'files' not in request.files:
        return error_response('No files provided', status=400)

    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return error_response('No files selected', status=400)

    uploaded_files = []
    upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'orders', str(order.id))
    os.makedirs(upload_dir, exist_ok=True)

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp to avoid collisions
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            file_path = os.path.join(upload_dir, unique_filename)

            try:
                file.save(file_path)

                # Create database record
                order_file = OrderFile(
                    order_id=order.id,
                    filename=unique_filename,
                    file_path=file_path,
                    is_from_client=True
                )
                db.session.add(order_file)
                uploaded_files.append({
                    'filename': unique_filename,
                    'size': order_file.file_size
                })

            except Exception as e:
                logger.error(f'Error uploading file: {str(e)}')
                continue

    db.session.commit()

    # Notify admin
    admins = User.query.filter_by(is_admin=True, is_active=True).all()
    for admin in admins:
        create_notification(
            user_id=admin.id,
            title=f'Files Uploaded - Order #{order.order_number}',
            message=f'Client uploaded {len(uploaded_files)} file(s) for order {order.title}',
            type=NotificationType.INFO,
            link=f'/admin/orders/{order.id}'
        )

    # Send email notification to admin
    from tuned.services.email_service import send_files_uploaded_email_admin
    send_files_uploaded_email_admin(order, uploaded_files)

    return created_response({
        'uploaded_files': uploaded_files,
        'count': len(uploaded_files)
    }, f'{len(uploaded_files)} file(s) uploaded successfully')
```

#### `GET /client/orders/<int:order_id>/files/<int:file_id>/download`

```python
# File: client/routes/orders/activities/files/download.py

from flask import send_file

@client_bp.route('/orders/<int:order_id>/files/<int:file_id>/download', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=100, window=3600)
def download_order_file(order_id, file_id):
    """Download an order file"""
    current_user_id = get_jwt_identity()

    # Verify order ownership
    order = Order.query.filter_by(
        id=order_id,
        client_id=current_user_id,
        is_active=True
    ).first()

    if not order:
        return not_found_response('Order not found')

    # Get file
    order_file = OrderFile.query.filter_by(id=file_id, order_id=order_id).first()

    if not order_file:
        return not_found_response('File not found')

    # Check file exists
    if not os.path.exists(order_file.file_path):
        return error_response('File not found on server', status=404)

    return send_file(
        order_file.file_path,
        as_attachment=True,
        download_name=order_file.filename
    )
```

#### `DELETE /client/orders/<int:order_id>/files/<int:file_id>`

```python
@client_bp.route('/orders/<int:order_id>/files/<int:file_id>', methods=['DELETE'])
@jwt_required()
@log_activity('file_deleted', 'OrderFile')
def delete_order_file(order_id, file_id):
    """Delete an order file (client can only delete their own uploads)"""
    current_user_id = get_jwt_identity()

    order = Order.query.filter_by(
        id=order_id,
        client_id=current_user_id,
        is_active=True
    ).first()

    if not order:
        return not_found_response('Order not found')

    order_file = OrderFile.query.filter_by(
        id=file_id,
        order_id=order_id,
        is_from_client=True  # Only client's own files
    ).first()

    if not order_file:
        return not_found_response('File not found or cannot be deleted')

    # Delete physical file
    try:
        if os.path.exists(order_file.file_path):
            os.remove(order_file.file_path)
    except Exception as e:
        logger.warning(f'Error deleting physical file: {str(e)}')

    # Delete database record
    db.session.delete(order_file)
    db.session.commit()

    return no_content_response()
```

---

### 4. Support Ticket Routes

#### `POST /client/orders/<int:order_id>/tickets`

```python
# File: client/routes/orders/activities/tickets/create.py

@client_bp.route('/orders/<int:order_id>/tickets', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=5, window=3600)  # 5 tickets per hour
@log_activity('support_ticket_created', 'SupportTicket')
def create_support_ticket(order_id):
    """Create a support ticket for an order"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    order = Order.query.filter_by(
        id=order_id,
        client_id=current_user_id,
        is_active=True
    ).first()

    if not order:
        return not_found_response('Order not found')

    schema = SupportTicketSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        return error_response('Validation failed', errors=e.messages, status=422)

    ticket = SupportTicket(
        order_id=order_id,
        user_id=current_user_id,
        subject=data['subject'],
        message=data['message'],
        status=SupportTicketStatus.OPEN
    )

    db.session.add(ticket)
    db.session.commit()

    # Notify admins
    admins = User.query.filter_by(is_admin=True, is_active=True).all()
    for admin in admins:
        create_notification(
            user_id=admin.id,
            title=f'New Support Ticket - Order #{order.order_number}',
            message=f'Subject: {data["subject"]}',
            type=NotificationType.WARNING,
            link=f'/admin/tickets/{ticket.id}'
        )

    # Send email
    from tuned.services.email_service import send_support_ticket_email_admin
    send_support_ticket_email_admin(ticket)

    return created_response({
        'id': ticket.id,
        'subject': ticket.subject,
        'status': ticket.status.value,
        'created_at': ticket.created_at.isoformat()
    }, 'Support ticket created successfully')
```

#### `GET /client/orders/<int:order_id>/tickets`

```python
# File: client/routes/orders/activities/tickets/get.py

@client_bp.route('/orders/<int:order_id>/tickets', methods=['GET'])
@jwt_required()
def get_order_tickets(order_id):
    """Get all support tickets for an order"""
    current_user_id = get_jwt_identity()

    order = Order.query.filter_by(
        id=order_id,
        client_id=current_user_id,
        is_active=True
    ).first()

    if not order:
        return not_found_response('Order not found')

    tickets = [{
        'id': t.id,
        'subject': t.subject,
        'message': t.message,
        'status': t.status.value,
        'created_at': t.created_at.isoformat(),
        'updated_at': t.updated_at.isoformat()
    } for t in order.support_tickets]

    return success_response(tickets)
```

---

### 5. Deadline Extension & Revision Routes

#### `POST /client/orders/<int:order_id>/extend-deadline`

```python
# File: client/routes/orders/activities/extend_deadline.py

@client_bp.route('/orders/<int:order_id>/extend-deadline', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=3, window=86400)  # 3 per day
@log_activity('deadline_extension_requested', 'Order')
def request_deadline_extension(order_id):
    """
    Request a deadline extension for an order.
    Note: Admin must approve the extension request.
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    order = Order.query.filter_by(
        id=order_id,
        client_id=current_user_id,
        is_active=True
    ).first()

    if not order:
        return not_found_response('Order not found')

    # Can only request extension for active orders
    if order.status not in [OrderStatus.ACTIVE, OrderStatus.PENDING]:
        return error_response('Cannot request extension for this order status', status=400)

    if order.extension_requested:
        return error_response('Extension already requested for this order', status=400)

    schema = ExtendDeadlineSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        return error_response('Validation failed', errors=e.messages, status=422)

    # Mark extension as requested
    order.extension_requested = True
    order.extension_requested_at = datetime.now(timezone.utc)
    db.session.commit()

    # Store extension request details (could use a separate table)
    # For now, use activity log
    ActivityLog.log(
        action='deadline_extension_requested',
        user_id=current_user_id,
        entity_type='Order',
        entity_id=order.id,
        description=f'Requested {data["requested_hours"]} hours extension',
        details=json.dumps({
            'requested_hours': data['requested_hours'],
            'reason': data['reason']
        })
    )

    # Notify admins
    admins = User.query.filter_by(is_admin=True, is_active=True).all()
    for admin in admins:
        create_notification(
            user_id=admin.id,
            title=f'Deadline Extension Request - Order #{order.order_number}',
            message=f'Client requests {data["requested_hours"]} hours extension',
            type=NotificationType.WARNING,
            link=f'/admin/orders/{order.id}'
        )

    # Send email
    from tuned.services.email_service import send_deadline_extension_request_email_admin
    send_deadline_extension_request_email_admin(order, data['requested_hours'], data['reason'])

    return success_response({
        'message': 'Extension request submitted successfully',
        'requested_hours': data['requested_hours']
    })
```

#### `POST /client/orders/<int:order_id>/request-revision`

```python
# File: client/routes/orders/activities/request_revision.py

@client_bp.route('/orders/<int:order_id>/request-revision', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=5, window=86400)  # 5 revisions per day max
@log_activity('revision_requested', 'Order')
def request_revision(order_id):
    """Request revision after order delivery"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    order = Order.query.filter_by(
        id=order_id,
        client_id=current_user_id,
        is_active=True
    ).first()

    if not order:
        return not_found_response('Order not found')

    # Can only request revision if order is COMPLETED_PENDING_REVIEW
    if order.status != OrderStatus.COMPLETED_PENDING_REVIEW:
        return error_response('Order must be delivered before requesting revision', status=400)

    schema = RequestRevisionSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        return error_response('Validation failed', errors=e.messages, status=422)

    # Verify delivery exists
    delivery = OrderDelivery.query.get(data['delivery_id'])
    if not delivery or delivery.order_id != order_id:
        return error_response('Invalid delivery ID', status=400)

    # Update order status to REVISION
    order.status = OrderStatus.REVISION
    db.session.commit()

    # Log revision request
    ActivityLog.log(
        action='revision_requested',
        user_id=current_user_id,
        entity_type='Order',
        entity_id=order.id,
        description='Client requested revision',
        details=json.dumps({
            'delivery_id': delivery.id,
            'revision_notes': data['revision_notes']
        })
    )

    # Notify admins
    admins = User.query.filter_by(is_admin=True, is_active=True).all()
    for admin in admins:
        create_notification(
            user_id=admin.id,
            title=f'Revision Requested - Order #{order.order_number}',
            message='Client has requested revisions to the delivery',
            type=NotificationType.WARNING,
            link=f'/admin/orders/{order.id}'
        )

    # Notify client
    create_notification(
        user_id=current_user_id,
        title=f'Revision Request Submitted',
        message=f'Your revision request for order #{order.order_number} has been submitted',
        type=NotificationType.INFO,
        link=f'/orders/{order.id}'
    )

    # Send emails
    from tuned.services.email_service import send_revision_request_email_admin, send_revision_request_email_client
    send_revision_request_email_admin(order, data['revision_notes'])
    send_revision_request_email_client(user, order)

    return success_response({
        'message': 'Revision request submitted successfully',
        'status': order.status.value
    })
```

---

**Due to length constraints, continuing in next response with:**

- Payment routes
- Settings routes
- Referral routes
- Email templates
- Celery tasks
- Testing
