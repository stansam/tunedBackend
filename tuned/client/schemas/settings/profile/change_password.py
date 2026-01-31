from marshmallow import Schema, fields, validates, validates_schema, ValidationError
from tuned.utils.validators import validate_password_strength


class ChangePasswordSchema(Schema):
    """Schema for changing user password."""
    current_password = fields.Str(required=True, load_only=True)
    new_password = fields.Str(required=True, load_only=True)
    confirm_password = fields.Str(required=True, load_only=True)
    
    @validates('current_password')
    def validate_current_password_field(self, value, **kwargs):
        """Ensure current password is provided."""
        if not value:
            raise ValidationError('Current password is required')
    
    @validates('new_password')
    def validate_new_password_field(self, value, **kwargs):
        """Validate new password strength."""
        is_valid, error = validate_password_strength(value)
        if not is_valid:
            raise ValidationError(error)
    
    @validates_schema
    def validate_passwords_match(self, data, **kwargs):
        """Validate that new passwords match."""
        if data.get('new_password') != data.get('confirm_password'):
            raise ValidationError({'confirm_password': ['Passwords do not match']})
        
        if data.get('current_password') == data.get('new_password'):
            raise ValidationError({'new_password': ['New password must be different from current password']})
