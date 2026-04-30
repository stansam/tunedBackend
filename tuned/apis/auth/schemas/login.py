from marshmallow import Schema, fields, validates, ValidationError
from tuned.utils.validators import validate_email
from typing import Any

class LoginSchema(Schema):
    identifier = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)
    remember_me = fields.Bool(load_default=False)
    
    @validates('identifier')
    def validate_identifier_field(self, value: str, **kwargs: Any) -> None:
        if not value or not value.strip():
            raise ValidationError('Email or username is required')
    
    @validates('password')
    def validate_password_field(self, value: str, **kwargs: Any) -> None:
        if not value:
            raise ValidationError('Password is required')
