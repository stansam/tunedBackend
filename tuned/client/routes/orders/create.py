"""
Order creation route for client blueprint.

Handles new order creation with pricing calculation, validation,
and notification dispatch.
"""

from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime, timedelta, timezone
import logging

from tuned.client import client_bp
from tuned.client.schemas import CreateOrderSchema
from tuned.models.order import Order
from tuned.models.service import Service, AcademicLevel, Deadline
from tuned.models.price import PriceRate
from tuned.models.payment import Invoice, Discount
from tuned.models.user import User
from tuned.extensions import db
from tuned.utils import (
    created_response, error_response, validation_error_response, not_found_response
)
from tuned.utils.decorators import rate_limit, log_activity
from tuned.services.notification_service import create_notification
from tuned.models.enums import NotificationType, OrderStatus, Currency
from tuned.tasks.order_tasks import send_payment_reminder

logger = logging.getLogger(__name__)


def calculate_order_price(service, academic_level, deadline, page_count):
    """
    Calculate the total price for an order based on service, academic level, deadline, and page count.
    
    Args:
        service: Service instance
        academic_level: AcademicLevel instance
        deadline: Deadline instance
        page_count: Number of pages (float)
        
    Returns:
        tuple: (price_per_page, subtotal, total_price)
    """
    # Find the pricing rate for this combination
    price_rate = PriceRate.query.filter_by(
        pricing_category_id=service.pricing_category_id,
        academic_level_id=academic_level.id,
        deadline_id=deadline.id,
        is_active=True
    ).first()
    
    if not price_rate:
        raise ValueError(
            f'No pricing found for service "{service.name}", '
            f'academic level "{academic_level.name}", '
            f'and deadline "{deadline.name}"'
        )
    
    price_per_page = price_rate.price_per_page
    subtotal = price_per_page * page_count
    
    ####### Future: Apply discounts here ###### 
    ###########################################

    total_price = subtotal
    
    return price_per_page, subtotal, total_price


# def generate_order_number():
#     """Generate a unique order number in format: ORD-YYYYMM-XXXX"""
#     from tuned.models.order import Order
    
#     now = datetime.now(timezone.utc)
#     prefix = now.strftime('ORD-%Y%m-')
    
#     # Get the count of orders this month
#     month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
#     count = Order.query.filter(
#         Order.created_at >= month_start
#     ).count()
    
#     order_number = f'{prefix}{count + 1:04d}'
#     return order_number


@client_bp.route('/orders/create', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=10, window=3600)  # 10 orders per hour
@log_activity('order_created', 'Order')
def create_order():
    """
    Create a new order for the authenticated client.
    
    Request Body:
        {
            "service_id": int,
            "academic_level_id": int,
            "deadline_id": int,
            "title": str (5-255 chars),
            "description": str (20-10000 chars),
            "word_count": int (250-50000),
            "page_count": float (1-200),
            "format_style": str (optional),
            "report_type": str (optional),
            "discount_code": str (optional),
            "additional_materials": str (optional)
        }
    
    Returns:
        201: Order created successfully
        400: Validation error or pricing unavailable
        404: Service, academic level, or deadline not found
        422: Invalid data format
    """
    current_user_id = get_jwt_identity()
    
    # Validate input
    schema = CreateOrderSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        logger.warning(f'Order creation validation failed for user {current_user_id}: {e.messages}')
        return validation_error_response(e.messages)
    except Exception as e:
        logger.error(f'Order creation error for user {current_user_id}: {str(e)}')
        return error_response('Invalid request data', status=400)
    
    try:
        # Validate service exists and is active
        service = Service.query.filter_by(
            id=data['service_id'],
            is_active=True
        ).first()
        
        if not service:
            return not_found_response('Service not found or inactive')
        
        # Validate academic level exists and is active
        academic_level = AcademicLevel.query.filter_by(
            id=data['academic_level_id'],
            is_active=True
        ).first()
        
        if not academic_level:
            return not_found_response('Academic level not found or inactive')
        
        # Validate deadline exists and is active
        deadline = Deadline.query.filter_by(
            id=data['deadline_id'],
            is_active=True
        ).first()
        
        if not deadline:
            return not_found_response('Deadline not found or inactive')
        
        # Calculate due date
        due_date = datetime.now(timezone.utc) + timedelta(hours=deadline.hours)
        
        # Calculate pricing
        try:
            price_per_page, subtotal, total_price = calculate_order_price(
                service, academic_level, deadline, data['page_count']
            )
        except ValueError as e:
            logger.error(f'Pricing calculation error: {str(e)}')
            return error_response(str(e), status=400)
        
        # Apply discount if provided
        discount_amount = 0.0
        discount_obj = None
        
        if data.get('discount_code'):
            discount_obj = Discount.query.filter_by(
                code=data['discount_code'].upper(),
                is_active=True
            ).first()
            
            if discount_obj and discount_obj.is_valid():
                if discount_obj.discount_type.value == 'percentage':
                    discount_amount = (discount_obj.value / 100) * subtotal
                else:  # fixed
                    discount_amount = discount_obj.value
                
                # Apply discount
                total_price = max(0, total_price - discount_amount)
                
                logger.info(f'Discount applied: {discount_obj.code} - ${discount_amount:.2f}')
        
        # Generate order number
        order_number = generate_order_number()
        
        # Create order
        order = Order(
            client_id=current_user_id,
            service_id=service.id,
            academic_level_id=academic_level.id,
            deadline_id=deadline.id,
            title=data['title'],
            description=data['description'],
            word_count=data['word_count'],
            page_count=data['page_count'],
            format_style=data.get('format_style'),
            report_type=data.get('report_type'),
            additional_materials=data.get('additional_materials'),
            price_per_page=price_per_page,
            subtotal=subtotal,
            discount_amount=discount_amount,
            total_price=total_price,
            currency=Currency.USD,
            due_date=due_date,
            status=OrderStatus.PENDING,
            paid=False,
            created_at=datetime.now(timezone.utc)
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create invoice
        invoice = Invoice(
            payment_id=None,  # Will be set when payment is made
            invoice_number=f'INV-{order.order_number}',
            subtotal=subtotal,
            discount=discount_amount,
            tax=0.0,  # Add tax calculation if needed
            total=total_price,
            due_date=due_date,
            paid=False
        )
        
        db.session.add(invoice)
        db.session.commit()
        
        logger.info(f'Order created: {order.id} ({order.order_number}) by user {current_user_id}')
        
        # Send notifications
        try:
            # Notify client
            create_notification(
                user_id=current_user_id,
                title='Order Created Successfully',
                message=f'Your order "{order.title}" has been created. Please complete payment to proceed.',
                type=NotificationType.INFO,
                link=f'/orders/{order.id}'
            )
            
            # Notify admins
            admins = User.query.filter_by(is_admin=True, is_active=True).all()
            for admin in admins:
                create_notification(
                    user_id=admin.id,
                    title=f'New Order - {order.order_number}',
                    message=f'New order "{order.title}" from {order.client.get_name()}',
                    type=NotificationType.INFO,
                    link=f'/admin/orders/{order.id}'
                )
        except Exception as e:
            logger.error(f'Notification error for order {order.id}: {str(e)}')
            # Don't fail the order creation if notifications fail
        
        # Schedule payment reminder (30 minutes)
        try:
            send_payment_reminder.apply_async(
                args=[order.id],
                countdown=1800  # 30 minutes
            )
        except Exception as e:
            logger.error(f'Failed to schedule payment reminder for order {order.id}: {str(e)}')
        
        # Send confirmation emails
        try:
            from tuned.services.email_service import send_order_created_email_client, send_order_created_email_admin
            
            user = User.query.get(current_user_id)
            send_order_created_email_client(user, order)
            send_order_created_email_admin(order)
        except Exception as e:
            logger.error(f'Email error for order {order.id}: {str(e)}')
            # Don't fail the order creation if emails fail
        
        # Prepare response data
        order_data = {
            'id': order.id,
            'order_number': order.order_number,
            'title': order.title,
            'description': order.description,
            'service': {
                'id': service.id,
                'name': service.name
            },
            'academic_level': {
                'id': academic_level.id,
                'name': academic_level.name
            },
            'deadline': {
                'id': deadline.id,
                'name': deadline.name,
                'hours': deadline.hours
            },
            'word_count': order.word_count,
            'page_count': order.page_count,
            'price_per_page': price_per_page,
            'subtotal': subtotal,
            'discount_amount': discount_amount,
            'total_price': total_price,
            'currency': order.currency.value,
            'due_date': due_date.isoformat(),
            'status': order.status.value,
            'paid': order.paid,
            'created_at': order.created_at.isoformat(),
            'payment_url': f'/orders/{order.id}/payment'
        }
        
        return created_response(
            data={'order': order_data},
            message='Order created successfully! Please complete payment within 30 minutes.'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Order creation error for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while creating your order. Please try again.', status=500)
