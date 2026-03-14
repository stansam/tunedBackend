"""
Invoice and receipt routes for client blueprint.

Handles invoice downloads and payment receipt generation.
"""

from flask import request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime, timezone
import io
import logging

from tuned.client import client_bp
from tuned.client.schemas import InvoiceDownloadSchema, PaymentReceiptSchema
from tuned.models.order import Order
from tuned.models.payment import Payment, Invoice
from tuned.extensions import db
from tuned.utils import success_response, error_response, validation_error_response
from tuned.utils.decorators import rate_limit
from tuned.services.pdf_service import generate_invoice_pdf, generate_receipt_pdf
from tuned.services.email_service import send_receipt_email

logger = logging.getLogger(__name__)


@client_bp.route('/orders/<int:order_id>/invoice', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=50, window=3600)
def download_invoice(order_id):
    """
    Download invoice for an order.
    
    Args:
        order_id: ID of the order
        
    Query Parameters:
        format: pdf or html (default: pdf)
        include_logo: Include company logo (default: true)
        language: Language for invoice (default: en)
    
    Returns:
        200: Invoice file
        404: Order or invoice not found
        403: Unauthorized access
    """
    current_user_id = get_jwt_identity()
    
    # Validate query parameters
    schema = InvoiceDownloadSchema()
    try:
        options = schema.load(request.args.to_dict())
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    try:
        # Verify order exists and user has access
        order = Order.query.filter_by(
            id=order_id,
            client_id=current_user_id,
            is_deleted=False
        ).first()
        
        if not order:
            return error_response('Order not found', status=404)
        
        # Get invoice - in a full implementation, get from Invoice model
        # For now, generate on the fly
        format_type = options.get('format', 'pdf')
        include_logo = options.get('include_logo', True)
        language = options.get('language', 'en')
        
        if format_type == 'pdf':
            # Generate PDF invoice
            try:
                pdf_buffer = generate_invoice_pdf(
                    order=order,
                    include_logo=include_logo,
                    language=language
                )
                
                filename = f'Invoice_{order.order_number}.pdf'
                
                logger.info(f'Invoice downloaded for order {order_id} by user {current_user_id}')
                
                return send_file(
                    pdf_buffer,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/pdf'
                )
                
            except Exception as e:
                logger.error(f'Error generating invoice PDF for order {order_id}: {str(e)}')
                return error_response('Failed to generate invoice', status=500)
        
        else:  # html
            # Return HTML invoice
            invoice_html = f"""
            <html>
            <head><title>Invoice - {order.order_number}</title></head>
            <body>
                <h1>Invoice</h1>
                <p>Order Number: {order.order_number}</p>
                <p>Total: ${order.total_price:.2f}</p>
                <!-- Full invoice HTML template -->
            </body>
            </html>
            """
            
            return invoice_html, 200, {'Content-Type': 'text/html'}
            
    except Exception as e:
        logger.error(f'Error downloading invoice for order {order_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while downloading the invoice', status=500)


@client_bp.route('/payments/<int:payment_id>/receipt', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=20, window=3600)
def get_payment_receipt(payment_id):
    """
    Generate and optionally email payment receipt.
    
    Args:
        payment_id: ID of the payment
        
    Request Body:
        {
            "format": str (pdf or email, default: pdf),
            "email": str (optional, required if format=email)
        }
    
    Returns:
        200: Receipt PDF file or confirmation that email was sent
        404: Payment not found
        403: Unauthorized access
        400: Validation error
    """
    current_user_id = get_jwt_identity()
    
    # Validate input
    schema = PaymentReceiptSchema()
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    try:
        # Get payment and verify ownership through order
        payment = db.session.query(Payment).join(
            Payment.order
        ).filter(
            Payment.id == payment_id,
            Payment.order.has(client_id=current_user_id)
        ).first()
        
        if not payment:
            return error_response('Payment not found', status=404)
        
        if payment.status.value != 'completed':
            return error_response('Receipt only available for completed payments', status=400)
        
        format_type = data.get('format', 'pdf')
        
        if format_type == 'email':
            # Send receipt via email
            email = data.get('email')
            if not email:
                return error_response('Email address is required when format is email', status=400)
            
            try:
                send_receipt_email(payment, email)
                
                logger.info(f'Receipt emailed for payment {payment_id} to {email}')
                
                return success_response(
                    message=f'Receipt sent successfully to {email}'
                )
                
            except Exception as e:
                logger.error(f'Error sending receipt email for payment {payment_id}: {str(e)}')
                return error_response('Failed to send receipt email', status=500)
        
        else:  # pdf
            # Generate PDF receipt
            try:
                pdf_buffer = generate_receipt_pdf(payment)
                
                filename = f'Receipt_{payment.transaction_id or payment.id}.pdf'
                
                logger.info(f'Receipt downloaded for payment {payment_id} by user {current_user_id}')
                
                return send_file(
                    pdf_buffer,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/pdf'
                )
                
            except Exception as e:
                logger.error(f'Error generating receipt PDF for payment {payment_id}: {str(e)}')
                return error_response('Failed to generate receipt', status=500)
            
    except Exception as e:
        logger.error(f'Error getting receipt for payment {payment_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while processing your request', status=500)


@client_bp.route('/orders/<int:order_id>/invoice-status', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=100, window=60)
def get_invoice_status(order_id):
    """
    Get invoice status for an order.
    
    Args:
        order_id: ID of the order
    
    Returns:
        200: Invoice status information
        404: Order not found
        403: Unauthorized access
    """
    current_user_id = get_jwt_identity()
    
    try:
        # Verify order and get invoice
        order = Order.query.filter_by(
            id=order_id,
            client_id=current_user_id,
            is_deleted=False
        ).first()
        
        if not order:
            return error_response('Order not found', status=404)
        
        # Calculate invoice details
        invoice_data = {
            'order_id': order.id,
            'order_number': order.order_number,
            'subtotal': float(order.subtotal),
            'discount': float(order.discount_amount) if order.discount_amount else 0.0,
            'tax': 0.0,  # Calculate tax if needed
            'total': float(order.total_price),
            'currency': order.currency.value if order.currency else 'USD',
            'paid': order.paid,
            'due_date': order.due_date.isoformat() if order.due_date else None,
            'created_at': order.created_at.isoformat()
        }
        
        return success_response(
            data={'invoice': invoice_data},
            message='Invoice status retrieved successfully'
        )
        
    except Exception as e:
        logger.error(f'Error getting invoice status for order {order_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while retrieving invoice status', status=500)
