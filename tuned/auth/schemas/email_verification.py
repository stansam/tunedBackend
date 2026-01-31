from marshmallow import Schema, fields, validates, ValidationError
from tuned.utils.validators import validate_email

class EmailVerificationSchema(Schema):
    """Schema for email verification."""
    token = fields.Str(required=True)
    
    @validates('token')
    def validate_token_field(self, value, **kwargs):
        """Basic token validation."""
        if not value or not value.strip():
            raise ValidationError('Verification token is required')


class ResendVerificationSchema(Schema):
    """Schema for resending verification email."""
    email = fields.Email(required=True)
    
    @validates('email')
    def validate_email_field(self, value, **kwargs):
        """Validate email format."""
        if not validate_email(value):
            raise ValidationError('Invalid email format')
