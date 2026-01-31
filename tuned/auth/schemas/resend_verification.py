"""
Schema for resending email verification.
"""
from marshmallow import Schema, fields


class ResendVerificationSchema(Schema):
    """Schema for resending verification email."""
    
    email = fields.Email(
        required=True,
        error_messages={
            'required': 'Email address is required',
            'invalid': 'Invalid email address format'
        }
    )
