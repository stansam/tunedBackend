"""
Validation schemas for deadline extension request operations.

Provides validation for deadline extension request creation and management.
"""
from marshmallow import Schema, fields, validates, ValidationError, validate


class CreateDeadlineExtensionRequestSchema(Schema):
    """Validation schema for creating a deadline extension request."""
    
    requested_hours = fields.Int(
        required=True,
        validate=validate.Range(min=12, max=720),  # 12 hours to 30 days
        error_messages={
            'required': 'Requested extension hours is required',
            'min': 'Minimum extension is 12 hours',
            'max': 'Maximum extension is 720 hours (30 days)'
        }
    )
    
    reason = fields.Str(
        required=True,
        validate=validate.Length(min=20, max=1000),
        error_messages={
            'required': 'Reason for extension is required',
            'min_length': 'Reason must be at least 20 characters',
            'max_length': 'Reason cannot exceed 1000 characters'
        }
    )


class UpdateDeadlineExtensionRequestSchema(Schema):
    """Validation schema for updating a deadline extension request (admin only)."""
    
    status = fields.Str(
        required=False,
        validate=validate.OneOf(['pending', 'approved', 'rejected', 'cancelled']),
        error_messages={'invalid': 'Invalid status value'}
    )
    
    admin_notes = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=2000),
        error_messages={'max_length': 'Admin notes cannot exceed 2000 characters'}
    )
    
    priority = fields.Str(
        required=False,
        validate=validate.OneOf(['low', 'normal', 'high', 'urgent']),
        error_messages={'invalid': 'Invalid priority value'}
    )
    
    rejection_reason = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(min=10, max=500),
        error_messages={
            'min_length': 'Rejection reason must be at least 10 characters',
            'max_length': 'Rejection reason cannot exceed 500 characters'
        }
    )
    
    approved_hours = fields.Int(
        required=False,
        allow_none=True,
        validate=validate.Range(min=1, max=720),
        error_messages={
            'min': 'Approved hours must be at least 1',
            'max': 'Approved hours cannot exceed 720 hours (30 days)'
        }
    )


class DeadlineExtensionFilterSchema(Schema):
    """Validation schema for filtering deadline extension requests."""
    
    status = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['pending', 'approved', 'rejected', 'cancelled'])
    )
    
    priority = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['low', 'normal', 'high', 'urgent'])
    )
    
    page = fields.Int(
        required=False,
        validate=validate.Range(min=1),
        error_messages={'invalid': 'Page must be a positive integer'}
    )
    
    per_page = fields.Int(
        required=False,
        validate=validate.Range(min=1, max=100),
        error_messages={'invalid': 'Per page must be between 1 and 100'}
    )
