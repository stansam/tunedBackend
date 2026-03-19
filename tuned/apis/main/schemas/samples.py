"""
Validation schemas for sample-related endpoints.

Includes schemas for:
- Sample filtering and pagination
"""
from marshmallow import Schema, fields, validate


class SampleFilterSchema(Schema):
    """Schema for filtering and paginating samples."""
    
    service_id = fields.Int(
        required=False,
        validate=validate.Range(min=1),
        error_messages={
            'invalid': 'Service ID must be an integer',
            'validator_failed': 'Service ID must be at least 1'
        }
    )
    
    featured = fields.Bool(
        required=False,
        error_messages={
            'invalid': 'Featured must be a boolean value'
        }
    )
    
    q = fields.Str(
        required=False,
        validate=validate.Length(min=2, max=200),
        error_messages={
            'invalid': 'Search query must be a string',
            'min': 'Search query must be at least 2 characters',
            'max': 'Search query must not exceed 200 characters'
        }
    )
    
    sort = fields.Str(
        required=False,
        validate=validate.OneOf(['created_at', 'word_count', 'title']),
        load_default='created_at',
        error_messages={
            'invalid': 'Sort field must be a string',
            'validator_failed': 'Sort must be one of: created_at, word_count, title'
        }
    )
    
    order = fields.Str(
        required=False,
        validate=validate.OneOf(['asc', 'desc']),
        load_default='desc',
        error_messages={
            'invalid': 'Order must be a string',
            'validator_failed': 'Order must be either asc or desc'
        }
    )
    
    page = fields.Int(
        required=False,
        validate=validate.Range(min=1),
        load_default=1,
        error_messages={
            'invalid': 'Page must be an integer',
            'validator_failed': 'Page must be at least 1'
        }
    )
    
    per_page = fields.Int(
        required=False,
        validate=validate.Range(min=1, max=100),
        load_default=20,
        error_messages={
            'invalid': 'Items per page must be an integer',
            'validator_failed': 'Items per page must be between 1 and 100'
        }
    )
