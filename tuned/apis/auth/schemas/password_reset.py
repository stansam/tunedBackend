from marshmallow import Schema, fields, validates, validates_schema, ValidationError
from tuned.utils.validators import validate_email, validate_password_strength
from typing import Any


class PasswordResetRequestSchema(Schema):
    email = fields.Email(required=True)
    
    @validates('email')
    def validate_email_field(self, value: str, **kwargs: Any) -> None:
        if not validate_email(value):
            raise ValidationError('Invalid email format')


class PasswordResetConfirmSchema(Schema):
    token = fields.Str(required=True)
    new_password = fields.Str(required=True, load_only=True)
    confirm_password = fields.Str(required=True, load_only=True)
    
    @validates('token')
    def validate_token_field(self, value: str, **kwargs: Any) -> None:
        if not value or not value.strip():
            raise ValidationError('Reset token is required')
    
    @validates('new_password')
    def validate_password_field(self, value: str, **kwargs: Any) -> None:
        is_valid, error = validate_password_strength(value)
        if not is_valid:
            raise ValidationError(error)
    
    @validates_schema
    def validate_passwords_match(self, data: dict, **kwargs: Any) -> None:
        if data.get('new_password') != data.get('confirm_password'):
            raise ValidationError({'confirm_password': ['Passwords do not match']})
