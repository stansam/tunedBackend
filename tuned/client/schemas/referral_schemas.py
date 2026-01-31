"""
Validation schemas for client referral operations.

This module contains Marshmallow schemas for validating client requests
related to referrals, reward points, and referral tracking.
"""

from marshmallow import Schema, fields, validates, ValidationError, validate, post_load
from tuned.models.enums import ReferralStatus
import re


class ReferralCodeSchema(Schema):
    """Validation schema for referral code operations."""
    
    referral_code = fields.Str(
        required=True,
        validate=validate.Length(equal=10),
        error_messages={
            'required': 'Referral code is required',
            'length': 'Referral code must be exactly 10 characters'
        }
    )
    
    @post_load
    def uppercase_code(self, data, **kwargs):
        """Convert referral code to uppercase."""
        if 'referral_code' in data:
            data['referral_code'] = data['referral_code'].upper().strip()
        return data


class ApplyReferralCodeSchema(Schema):
    """Validation schema for applying a referral code during registration."""
    
    code = fields.Str(
        required=True,
        validate=validate.Length(min=6, max=20),
        error_messages={
            'required': 'Referral code is required',
            'min_length': 'Referral code is too short',
            'max_length': 'Referral code is too long'
        }
    )
    
    @post_load
    def clean_code(self, data, **kwargs):
        """Clean and validate referral code format."""
        if 'code' in data:
            # Remove any whitespace and convert to uppercase
            code = data['code'].upper().strip()
            
            # Validate format (alphanumeric only)
            if not re.match(r'^[A-Z0-9]+$', code):
                raise ValidationError({
                    'code': ['Referral code must contain only letters and numbers']
                })
            
            data['code'] = code
        
        return data


class RedeemRewardSchema(Schema):
    """Validation schema for redeeming reward points."""
    
    points = fields.Int(
        required=True,
        validate=validate.Range(min=100, max=100000),
        error_messages={
            'required': 'Points to redeem is required',
            'min': 'Minimum redemption is 100 points',
            'max': 'Maximum redemption is 100000 points'
        }
    )
    
    order_id = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        error_messages={'required': 'Order ID is required'}
    )
    
    @validates('points')
    def validate_points_multiple(self, value):
        """Ensure points are in multiples of 100."""
        if value % 100 != 0:
            raise ValidationError('Points must be in multiples of 100')


class ReferralFilterSchema(Schema):
    """Validation schema for filtering referrals list."""
    
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
    
    status = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf([s.value for s in ReferralStatus])
    )
    
    sort_by = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['created_at', 'commission', 'status'])
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


class ReferralEarningsSchema(Schema):
    """Validation schema for tracking referral earnings."""
    
    start_date = fields.DateTime(
        required=False,
        allow_none=True,
        format='iso'
    )
    
    end_date = fields.DateTime(
        required=False,
        allow_none=True,
        format='iso'
    )
    
    group_by = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['day', 'week', 'month', 'year'])
    )
    
    @post_load
    def set_defaults(self, data, **kwargs):
        """Set default values."""
        data.setdefault('group_by', 'month')
        return data


class WithdrawReferralEarningsSchema(Schema):
    """Validation schema for withdrawing referral earnings."""
    
    amount = fields.Float(
        required=True,
        validate=validate.Range(min=10.00, max=10000.00),
        error_messages={
            'required': 'Withdrawal amount is required',
            'min': 'Minimum withdrawal is $10.00',
            'max': 'Maximum withdrawal is $10,000.00'
        }
    )
    
    withdrawal_method = fields.Str(
        required=True,
        validate=validate.OneOf(['paypal', 'bank_transfer', 'check', 'store_credit']),
        error_messages={'required': 'Withdrawal method is required'}
    )
    
    paypal_email = fields.Email(
        required=False,
        allow_none=True
    )
    
    bank_account_details = fields.Dict(
        required=False,
        allow_none=True
    )
    
    mailing_address = fields.Dict(
        required=False,
        allow_none=True
    )
    
    @validates('paypal_email')
    def validate_paypal_email(self, value):
        """Ensure PayPal email is provided if withdrawal method is PayPal."""
        if hasattr(self, 'withdrawal_method') and self.withdrawal_method == 'paypal':
            if not value:
                raise ValidationError('PayPal email is required for PayPal withdrawals')
    
    @validates('bank_account_details')
    def validate_bank_details(self, value):
        """Ensure bank details are provided if withdrawal method is bank transfer."""
        if hasattr(self, 'withdrawal_method') and self.withdrawal_method == 'bank_transfer':
            if not value or not isinstance(value, dict):
                raise ValidationError('Bank account details are required for bank transfers')
            
            required_fields = ['account_holder', 'account_number', 'routing_number', 'bank_name']
            for field in required_fields:
                if field not in value or not value[field]:
                    raise ValidationError({
                        'bank_account_details': [f'{field} is required in bank account details']
                    })
    
    @validates('mailing_address')
    def validate_mailing_address(self, value):
        """Ensure mailing address is provided if withdrawal method is check."""
        if hasattr(self, 'withdrawal_method') and self.withdrawal_method == 'check':
            if not value or not isinstance(value, dict):
                raise ValidationError('Mailing address is required for check withdrawals')
            
            required_fields = ['street', 'city', 'state', 'zip_code', 'country']
            for field in required_fields:
                if field not in value or not value[field]:
                    raise ValidationError({
                        'mailing_address': [f'{field} is required in mailing address']
                    })


class ReferralShareSchema(Schema):
    """Validation schema for sharing referral links."""
    
    share_method = fields.Str(
        required=True,
        validate=validate.OneOf(['email', 'sms', 'whatsapp', 'facebook', 'twitter', 'copy_link']),
        error_messages={'required': 'Share method is required'}
    )
    
    recipient_email = fields.Email(
        required=False,
        allow_none=True
    )
    
    recipient_phone = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Regexp(
            r'^\+?[1-9]\d{1,14}$',
            error='Invalid phone number format'
        )
    )
    
    custom_message = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=500)
    )
    
    @validates('recipient_email')
    def validate_email_for_email_share(self, value):
        """Ensure email is provided for email sharing."""
        if hasattr(self, 'share_method') and self.share_method == 'email':
            if not value:
                raise ValidationError('Recipient email is required for email sharing')
    
    @validates('recipient_phone')
    def validate_phone_for_sms_share(self, value):
        """Ensure phone is provided for SMS sharing."""
        if hasattr(self, 'share_method') and self.share_method in ['sms', 'whatsapp']:
            if not value:
                raise ValidationError('Recipient phone is required for SMS/WhatsApp sharing')


class RewardPointsTransferSchema(Schema):
    """Validation schema for transferring reward points to another user."""
    
    recipient_email = fields.Email(
        required=True,
        error_messages={'required': 'Recipient email is required'}
    )
    
    points = fields.Int(
        required=True,
        validate=validate.Range(min=50, max=10000),
        error_messages={
            'required': 'Points to transfer is required',
            'min': 'Minimum transfer is 50 points',
            'max': 'Maximum transfer is 10000 points'
        }
    )
    
    message = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=200)
    )
    
    @validates('points')
    def validate_points_multiple(self, value):
        """Ensure points are in multiples of 50."""
        if value % 50 != 0:
            raise ValidationError('Points must be in multiples of 50')


class ReferralStatsFilterSchema(Schema):
    """Validation schema for filtering referral statistics."""
    
    period = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['today', 'this_week', 'this_month', 'this_year', 'all_time'])
    )
    
    metric = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['all', 'signups', 'conversions', 'earnings', 'active'])
    )
    
    @post_load
    def set_defaults(self, data, **kwargs):
        """Set default values."""
        data.setdefault('period', 'all_time')
        data.setdefault('metric', 'all')
        return data
