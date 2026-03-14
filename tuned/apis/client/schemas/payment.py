"""
Validation schemas for client payment operations.

This module contains Marshmallow schemas for validating client requests
related to payments, invoices, and payment confirmations.
"""

from marshmallow import Schema, fields, validates, ValidationError, validate, post_load
from tuned.models.enums import PaymentStatus, PaymentMethod


class PaymentFilterSchema(Schema):
    """Validation schema for filtering and paginating payments list."""
    
    page = fields.Int(
        required=False,
        allow_none=True,
        validate=validate.Range(min=1, max=10000),
        error_messages={'invalid': 'Page must be a positive integer'}
    )
    
    per_page = fields.Int(
        required=False,
        allow_none=True,
        validate=validate.Range(min=1, max=100),
        error_messages={'invalid': 'Items per page must be between 1 and 100'}
    )
    
    status = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf([s.value for s in PaymentStatus])
    )
    
    method = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf([m.value for m in PaymentMethod])
    )
    
    order_id = fields.Int(
        required=False,
        allow_none=True,
        validate=validate.Range(min=1)
    )
    
    sort_by = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['created_at', 'amount', 'paid_at', 'status'])
    )
    
    sort_order = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['asc', 'desc'])
    )
    
    from_date = fields.DateTime(
        required=False,
        allow_none=True,
        format='iso'
    )
    
    to_date = fields.DateTime(
        required=False,
        allow_none=True,
        format='iso'
    )
    
    @post_load
    def set_defaults(self, data, **kwargs):
        """Set default values."""
        data.setdefault('page', 1)
        data.setdefault('per_page', 10)
        data.setdefault('sort_by', 'created_at')
        data.setdefault('sort_order', 'desc')
        return data


class ManualPaymentConfirmationSchema(Schema):
    """
    Validation schema for manual payment confirmation submission.
    Used when client pays via bank transfer or other offline methods.
    """
    
    order_id = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        error_messages={'required': 'Order ID is required'}
    )
    
    payment_method = fields.Str(
        required=True,
        validate=validate.OneOf([m.value for m in PaymentMethod]),
        error_messages={'required': 'Payment method is required'}
    )
    
    payer_email = fields.Email(
        required=True,
        error_messages={'required': 'Payer email is required'}
    )
    
    amount = fields.Float(
        required=True,
        validate=validate.Range(min=0.01, max=1000000),
        error_messages={
            'required': 'Payment amount is required',
            'min': 'Amount must be greater than 0',
            'max': 'Amount exceeds maximum allowed'
        }
    )
    
    transaction_reference = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
        error_messages={'max_length': 'Transaction reference is too long'}
    )
    
    transaction_date = fields.DateTime(
        required=False,
        allow_none=True,
        format='iso'
    )
    
    notes = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=1000),
        error_messages={'max_length': 'Notes cannot exceed 1000 characters'}
    )
    
    proof_of_payment = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=500),
        error_messages={'max_length': 'Proof of payment path is too long'}
    )
    
    @post_load
    def validate_payment_data(self, data, **kwargs):
        """Additional validation after loading."""
        # Ensure transaction_reference is provided for certain payment methods
        if data.get('payment_method') in ['bank_transfer', 'wire_transfer']:
            if not data.get('transaction_reference'):
                raise ValidationError({
                    'transaction_reference': ['Transaction reference is required for bank/wire transfers']
                })
        return data


class PayPalPaymentSchema(Schema):
    """Validation schema for PayPal payment confirmation."""
    
    order_id = fields.Int(
        required=True,
        validate=validate.Range(min=1)
    )
    
    paypal_order_id = fields.Str(
        required=True,
        validate=validate.Length(min=5, max=100)
    )
    
    payer_id = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100)
    )
    
    payment_source = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['paypal', 'card', 'bank'])
    )


class BraintreePaymentSchema(Schema):
    """Validation schema for Braintree payment submission."""
    
    order_id = fields.Int(
        required=True,
        validate=validate.Range(min=1)
    )
    
    payment_method_nonce = fields.Str(
        required=True,
        validate=validate.Length(min=10, max=200),
        error_messages={'required': 'Payment method nonce is required'}
    )
    
    device_data = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=5000)
    )
    
    billing_address = fields.Dict(
        required=False,
        allow_none=True
    )


class InvoiceDownloadSchema(Schema):
    """Validation schema for invoice download requests."""
    
    format = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['pdf', 'html'])
    )
    
    include_logo = fields.Boolean(
        required=False,
        allow_none=True
    )
    
    language = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['en', 'es', 'fr', 'de'])
    )
    
    @post_load
    def set_defaults(self, data, **kwargs):
        """Set default values."""
        data.setdefault('format', 'pdf')
        data.setdefault('include_logo', True)
        data.setdefault('language', 'en')
        return data


class PaymentReceiptSchema(Schema):
    """Validation schema for payment receipt requests."""
    
    payment_id = fields.Int(
        required=True,
        validate=validate.Range(min=1)
    )
    
    format = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['pdf', 'email'])
    )
    
    email = fields.Email(
        required=False,
        allow_none=True
    )
    
    @post_load
    def set_defaults(self, data, **kwargs):
        """Set default values."""
        data.setdefault('format', 'pdf')
        return data
    
    @validates('email')
    def validate_email_for_format(self, value):
        """Ensure email is provided if format is 'email'."""
        if hasattr(self, 'format') and self.format == 'email' and not value:
            raise ValidationError('Email is required when format is set to email')


class RefundRequestSchema(Schema):
    """Validation schema for payment refund requests."""
    
    payment_id = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        error_messages={'required': 'Payment ID is required'}
    )
    
    reason = fields.Str(
        required=True,
        validate=validate.Length(min=20, max=1000),
        error_messages={
            'required': 'Refund reason is required',
            'min_length': 'Please provide a detailed reason (minimum 20 characters)',
            'max_length': 'Reason cannot exceed 1000 characters'
        }
    )
    
    refund_type = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['full', 'partial'])
    )
    
    refund_amount = fields.Float(
        required=False,
        allow_none=True,
        validate=validate.Range(min=0.01)
    )
    
    @post_load
    def set_defaults(self, data, **kwargs):
        """Set default values."""
        data.setdefault('refund_type', 'full')
        return data
    
    @validates('refund_amount')
    def validate_refund_amount(self, value):
        """Ensure refund amount is provided for partial refunds."""
        if hasattr(self, 'refund_type') and self.refund_type == 'partial':
            if not value or value <= 0:
                raise ValidationError('Refund amount is required for partial refunds')


class DiscountCodeSchema(Schema):
    """Validation schema for applying discount codes."""
    
    code = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=50),
        error_messages={
            'required': 'Discount code is required',
            'min_length': 'Discount code is too short',
            'max_length': 'Discount code is too long'
        }
    )
    
    order_id = fields.Int(
        required=False,
        allow_none=True,
        validate=validate.Range(min=1)
    )
    
    @post_load
    def uppercase_code(self, data, **kwargs):
        """Convert discount code to uppercase."""
        if 'code' in data:
            data['code'] = data['code'].upper().strip()
        return data


class PaymentMethodSchema(Schema):
    """Validation schema for saving payment methods."""
    
    payment_method_type = fields.Str(
        required=True,
        validate=validate.OneOf(['credit_card', 'paypal', 'bank_account'])
    )
    
    is_default = fields.Boolean(
        required=False,
        allow_none=True
    )
    
    billing_address = fields.Dict(
        required=False,
        allow_none=True
    )
    
    # For credit cards
    card_last_four = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(equal=4)
    )
    
    card_type = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['visa', 'mastercard', 'amex', 'discover'])
    )
    
    expiry_month = fields.Int(
        required=False,
        allow_none=True,
        validate=validate.Range(min=1, max=12)
    )
    
    expiry_year = fields.Int(
        required=False,
        allow_none=True,
        validate=validate.Range(min=2024, max=2050)
    )
    
    @post_load
    def set_defaults(self, data, **kwargs):
        """Set default values."""
        data.setdefault('is_default', False)
        return data


class TransactionFilterSchema(Schema):
    """Validation schema for filtering transactions."""
    
    page = fields.Int(
        required=False,
        allow_none=True,
        validate=validate.Range(min=1)
    )
    
    per_page = fields.Int(
        required=False,
        allow_none=True,
        validate=validate.Range(min=1, max=100)
    )
    
    payment_id = fields.Int(
        required=False,
        allow_none=True,
        validate=validate.Range(min=1)
    )
    
    transaction_type = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['charge', 'refund', 'authorization', 'capture'])
    )
    
    from_date = fields.DateTime(
        required=False,
        allow_none=True,
        format='iso'
    )
    
    to_date = fields.DateTime(
        required=False,
        allow_none=True,
        format='iso'
    )
    
    @post_load
    def set_defaults(self, data, **kwargs):
        """Set default values."""
        data.setdefault('page', 1)
        data.setdefault('per_page', 20)
        return data
