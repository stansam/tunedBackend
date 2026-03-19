"""
Validation schemas for client order operations.

This module contains Marshmallow schemas for validating client requests
related to order creation, listing, filtering, comments, and other order activities.
"""

from marshmallow import Schema, fields, validates, ValidationError, validate, post_load
from tuned.models.enums import OrderStatus
from datetime import datetime


class CreateOrderSchema(Schema):
    """Validation schema for creating a new order."""
    
    service_id = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        error_messages={'required': 'Service is required'}
    )
    
    academic_level_id = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        error_messages={'required': 'Academic level is required'}
    )
    
    deadline_id = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        error_messages={'required': 'Deadline is required'}
    )
    
    title = fields.Str(
        required=True,
        validate=validate.Length(min=5, max=255),
        error_messages={
            'required': 'Order title is required',
            'min_length': 'Title must be at least 5 characters',
            'max_length': 'Title cannot exceed 255 characters'
        }
    )
    
    description = fields.Str(
        required=True,
        validate=validate.Length(min=20, max=10000),
        error_messages={
            'required': 'Order description is required',
            'min_length': 'Description must be at least 20 characters',
            'max_length': 'Description cannot exceed 10000 characters'
        }
    )
    
    word_count = fields.Int(
        required=True,
        validate=validate.Range(min=250, max=50000),
        error_messages={
            'required': 'Word count is required',
            'min': 'Minimum word count is 250',
            'max': 'Maximum word count is 50000'
        }
    )
    
    page_count = fields.Float(
        required=True,
        validate=validate.Range(min=1, max=200),
        error_messages={
            'required': 'Page count is required',
            'min': 'Minimum page count is 1',
            'max': 'Maximum page count is 200'
        }
    )
    
    format_style = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(
            ['APA', 'MLA', 'Chicago', 'Harvard', 'Turabian', 'IEEE', 'AMA'],
            error='Invalid format style'
        )
    )
    
    report_type = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100)
    )
    
    discount_code = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=50)
    )
    
    additional_materials = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=2000)
    )
    
    @validates('page_count')
    def validate_page_count(self, value):
        """Ensure page count is reasonable given word count."""
        # Approximate: 250-300 words per page
        # This validation happens after word_count is loaded
        if hasattr(self, 'word_count'):
            min_pages = self.word_count / 300
            max_pages = self.word_count / 250
            if not (min_pages * 0.8 <= value <= max_pages * 1.2):
                raise ValidationError(
                    f'Page count seems inconsistent with word count. '
                    f'Expected approximately {min_pages:.1f} to {max_pages:.1f} pages.'
                )


class OrderFilterSchema(Schema):
    """Validation schema for filtering and paginating orders list."""
    
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
        validate=validate.OneOf([s.value for s in OrderStatus])
    )
    
    search = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255)
    )
    
    sort_by = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf([
            'created_at', 'due_date', 'total_price', 
            'status', 'title', 'updated_at'
        ])
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
        """Set default values for optional fields."""
        data.setdefault('page', 1)
        data.setdefault('per_page', 10)
        data.setdefault('sort_by', 'created_at')
        data.setdefault('sort_order', 'desc')
        return data
    
    @validates('to_date')
    def validate_date_range(self, value):
        """Ensure to_date is after from_date."""
        if value and hasattr(self, 'from_date') and self.from_date:
            if value < self.from_date:
                raise ValidationError('End date must be after start date')


class OrderCommentSchema(Schema):
    """Validation schema for adding comments to an order."""
    
    message = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=5000),
        error_messages={
            'required': 'Comment message is required',
            'min_length': 'Comment cannot be empty',
            'max_length': 'Comment cannot exceed 5000 characters'
        }
    )
    
    @post_load
    def strip_message(self, data, **kwargs):
        """Strip whitespace from message."""
        if 'message' in data:
            data['message'] = data['message'].strip()
            if not data['message']:
                raise ValidationError({'message': ['Comment cannot be empty']})
        return data


class UpdateOrderCommentSchema(Schema):
    """Validation schema for updating an existing comment."""
    
    message = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=5000),
        error_messages={
            'required': 'Comment message is required',
            'min_length': 'Comment cannot be empty',
            'max_length': 'Comment cannot exceed 5000 characters'
        }
    )


class ExtendDeadlineSchema(Schema):
    """Validation schema for deadline extension requests."""
    
    requested_hours = fields.Int(
        required=True,
        validate=validate.Range(min=12, max=720),
        error_messages={
            'required': 'Extension hours is required',
            'min': 'Minimum extension is 12 hours',
            'max': 'Maximum extension is 720 hours (30 days)'
        }
    )
    
    reason = fields.Str(
        required=True,
        validate=validate.Length(min=20, max=500),
        error_messages={
            'required': 'Reason for extension is required',
            'min_length': 'Reason must be at least 20 characters',
            'max_length': 'Reason cannot exceed 500 characters'
        }
    )


class RequestRevisionSchema(Schema):
    """Validation schema for requesting order revision."""
    
    delivery_id = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        error_messages={'required': 'Delivery ID is required'}
    )
    
    revision_notes = fields.Str(
        required=True,
        validate=validate.Length(min=20, max=2000),
        error_messages={
            'required': 'Revision notes are required',
            'min_length': 'Please provide detailed revision notes (minimum 20 characters)',
            'max_length': 'Revision notes cannot exceed 2000 characters'
        }
    )


class SupportTicketSchema(Schema):
    """Validation schema for creating support tickets."""
    
    subject = fields.Str(
        required=True,
        validate=validate.Length(min=5, max=255),
        error_messages={
            'required': 'Subject is required',
            'min_length': 'Subject must be at least 5 characters',
            'max_length': 'Subject cannot exceed 255 characters'
        }
    )
    
    message = fields.Str(
        required=True,
        validate=validate.Length(min=20, max=5000),
        error_messages={
            'required': 'Message is required',
            'min_length': 'Message must be at least 20 characters',
            'max_length': 'Message cannot exceed 5000 characters'
        }
    )
    
    priority = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['low', 'normal', 'high', 'urgent'])
    )


class AcceptDeliverySchema(Schema):
    """Validation schema for accepting order delivery."""
    
    delivery_id = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        error_messages={'required': 'Delivery ID is required'}
    )
    
    rating = fields.Int(
        allow_none=True,
        validate=validate.Range(min=1, max=5)
    )
    
    feedback = fields.Str(
        allow_none=True,
        validate=validate.Length(max=1000)
    )


class FileUploadSchema(Schema):
    """Validation schema for file upload metadata."""
    
    description = fields.Str(
        allow_none=True,
        validate=validate.Length(max=500)
    )
    
    file_category = fields.Str(
        allow_none=True,
        validate=validate.OneOf(['requirement', 'reference', 'sample', 'other'])
    )
