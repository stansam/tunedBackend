"""
Validation schemas for revision request operations.

Provides validation for revision request creation and management.
"""
from marshmallow import Schema, fields, validates, ValidationError, validate


class CreateRevisionRequestSchema(Schema):
    """Validation schema for creating a revision request."""
    
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
            'min_length': 'Revision notes must be at least 20 characters',
            'max_length': 'Revision notes cannot exceed 2000 characters'
        }
    )


class UpdateRevisionRequestSchema(Schema):
    """Validation schema for updating a revision request (admin only)."""
    
    status = fields.Str(
        required=False,
        validate=validate.OneOf([
            'pending', 'in_progress', 'completed', 'rejected', 'cancelled'
        ]),
        error_messages={'invalid': 'Invalid status value'}
    )
    
    internal_notes = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=2000),
        error_messages={'max_length': 'Internal notes cannot exceed 2000 characters'}
    )
    
    priority = fields.Str(
        required=False,
        validate=validate.OneOf(['low', 'normal', 'high', 'urgent']),
        error_messages={'invalid': 'Invalid priority value'}
    )
    
    estimated_completion = fields.DateTime(
        required=False,
        allow_none=True,
        format='iso',
        error_messages={'invalid': 'Invalid datetime format. Use ISO 8601 format.'}
    )


class RevisionRequestFilterSchema(Schema):
    """Validation schema for filtering revision requests."""
    
    status = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf([
            'pending', 'in_progress', 'completed', 'rejected', 'cancelled'
        ])
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
