from marshmallow import Schema, fields, validates, validates_schema, ValidationError
from tuned.models.user import User, GenderEnum
from tuned.utils.validators import validate_email, validate_password_strength, validate_username, validate_phone_number


class RegistrationSchema(Schema):
    """Schema for user registration."""
    username = fields.Str(required=True)
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)
    confirm_password = fields.Str(required=True, load_only=True)
    first_name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    gender = fields.Str(required=True)
    phone_number = fields.Str(required=False, allow_none=True)
    
    @validates('username')
    def validate_username_field(self, value, **kwargs):
        """Validate username format and uniqueness."""
        is_valid, error = validate_username(value)
        if not is_valid:
            raise ValidationError(error)
        
        if User.query.filter_by(username=value).first():
            raise ValidationError('Username already exists')
    
    @validates('email')
    def validate_email_field(self, value, **kwargs):
        """Validate email format and uniqueness."""
        if not validate_email(value):
            raise ValidationError('Invalid email format')
        
        if User.query.filter_by(email=value).first():
            raise ValidationError('Email already exists')
    
    @validates('password')
    def validate_password_field(self, value, **kwargs):
        """Validate password strength."""
        is_valid, error = validate_password_strength(value)
        if not is_valid:
            raise ValidationError(error)
    
    @validates('gender')
    def validate_gender_field(self, value, **kwargs):
        """Validate gender value."""
        if value.lower() not in GenderEnum:
            raise ValidationError('Gender must be either "male" or "female"')
    
    @validates('phone_number')
    def validate_phone_field(self, value, **kwargs):
        """Validate phone number format if provided."""
        if value and not validate_phone_number(value):
            raise ValidationError('Invalid phone number format. Use international format (e.g., +1234567890)')
    
    @validates_schema
    def validate_passwords_match(self, data, **kwargs):
        """Validate that password and confirm_password match."""
        if data.get('password') != data.get('confirm_password'):
            raise ValidationError({'confirm_password': ['Passwords do not match']})
