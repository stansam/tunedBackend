from marshmallow import Schema, fields, validates, ValidationError
from tuned.utils.validators import validate_email
from tuned.models.user import User

class ChangeEmailSchema(Schema):
    """Schema for changing user email."""
    new_email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)
    
    @validates('new_email')
    def validate_new_email_field(self, value, **kwargs):
        """Validate new email format and uniqueness."""
        if not validate_email(value):
            raise ValidationError('Invalid email format')
        
        if User.query.filter_by(email=value).first():
            raise ValidationError('Email already in use')
    
    @validates('password')
    def validate_password_field(self, value, **kwargs):
        """Ensure password is provided."""
        if not value:
            raise ValidationError('Password is required to change email')

