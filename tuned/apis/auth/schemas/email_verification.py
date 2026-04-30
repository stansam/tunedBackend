from marshmallow import Schema, fields, validates, ValidationError
from tuned.utils.validators import validate_email
from typing import Any


class EmailVerifyResendSchema(Schema):
    email = fields.Email(required=True, error_messages={
        'required': 'Email address is required.',
        'invalid': 'Please provide a valid email address.',
    })

    @validates('email')
    def validate_email_field(self, value: str, **kwargs: Any) -> None:
        if not validate_email(value):
            raise ValidationError('Please provide a valid email address.')


class EmailVerifyConfirmSchema(Schema):
    uid = fields.Str(required=True, error_messages={
        'required': 'User identifier (uid) is required.',
    })
    token = fields.Str(required=True, error_messages={
        'required': 'Verification token is required.',
    })

    @validates('uid')
    def validate_uid(self, value: str, **kwargs: Any) -> None:
        if not value or len(value.strip()) == 0:
            raise ValidationError('User identifier must not be empty.')

    @validates('token')
    def validate_token(self, value: str, **kwargs: Any) -> None:
        if len(value) < 40:
            raise ValidationError('Token appears to be malformed.')
