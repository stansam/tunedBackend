"""
Validation schemas for service-related endpoints.

Includes schemas for:
- Service filtering and pagination
"""
from marshmallow import Schema, fields, validate


class ServiceFilterSchema(Schema):
    """Schema for filtering and paginating services."""
    
    category_id = fields.Int(
        required=False,
        validate=validate.Range(min=1),
        error_messages={
            'invalid': 'Category ID must be an integer',
            'validator_failed': 'Category ID must be at least 1'
        }
    )
    
    featured = fields.Bool(
        required=False,
        error_messages={
            'invalid': 'Featured must be a boolean value'
        }
    )
    
    is_active = fields.Bool(
        required=False,
        load_default=True,
        error_messages={
            'invalid': 'Active status must be a boolean value'
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
        validate=validate.OneOf(['name', 'created_at', 'category']),
        load_default='name',
        error_messages={
            'invalid': 'Sort field must be a string',
            'validator_failed': 'Sort must be one of: name, created_at, category'
        }
    )
    
    order = fields.Str(
        required=False,
        validate=validate.OneOf(['asc', 'desc']),
        load_default='asc',
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
