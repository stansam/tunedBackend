from marshmallow import Schema, fields, validates, validates_schema, ValidationError
from tuned.utils.validators import validate_email, validate_password_strength


class PasswordResetRequestSchema(Schema):
    """Schema for password reset request."""
    email = fields.Email(required=True)
    
    @validates('email')
    def validate_email_field(self, value, **kwargs):
        """Validate email format."""
        if not validate_email(value):
            raise ValidationError('Invalid email format')


class PasswordResetConfirmSchema(Schema):
    """Schema for password reset confirmation."""
    token = fields.Str(required=True)
    new_password = fields.Str(required=True, load_only=True)
    confirm_password = fields.Str(required=True, load_only=True)
    
    @validates('token')
    def validate_token_field(self, value, **kwargs):
        """Basic token validation."""
        if not value or not value.strip():
            raise ValidationError('Reset token is required')
    
    @validates('new_password')
    def validate_password_field(self, value, **kwargs):
        """Validate new password strength."""
        is_valid, error = validate_password_strength(value)
        if not is_valid:
            raise ValidationError(error)
    
    @validates_schema
    def validate_passwords_match(self, data, **kwargs):
        """Validate that passwords match."""
        if data.get('new_password') != data.get('confirm_password'):
            raise ValidationError({'confirm_password': ['Passwords do not match']})
