from marshmallow import Schema, fields, validates, validates_schema, ValidationError, pre_load
from marshmallow.validate import Length
from typing import Any
from tuned.models.user import User
from tuned.utils.validators import validate_email, validate_password_strength, validate_username, validate_phone_number

class RegistrationSchema(Schema):
    username = fields.Str(required=True, validate=Length(min=3))
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True, validate=Length(min=8))
    confirm_password = fields.Str(required=True, load_only=True)
    first_name = fields.String(required=True)
    last_name = fields.String(required=True)
    gender = fields.Str(required=True)
    phone_number = fields.Str(required=False, allow_none=True)
    referred_by_code = fields.Str(required=False, allow_none=True)

    @pre_load
    def handle_name_and_gender(self, data: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        if "name" in data and not data.get("first_name"):
            name_parts = data.pop("name")
            parts = name_parts.strip().split(maxsplit=1)
            data["first_name"] = parts[0]
            data["last_name"] = parts[1] if len(parts) > 1 else ""
            
        if "gender" in data:
            val = str(data["gender"]).lower()
            if val in ("m", "male"):
                data["gender"] = "male"
            elif val in ("f", "female"):
                data["gender"] = "female"
            else:
                data["gender"] = "unknown"
        return data
    
    @validates('username')
    def validate_username_field(self, value: str, **kwargs: Any) -> None:
        is_valid, error = validate_username(value)
        if not is_valid:
            raise ValidationError(error or "Invalid username")
        
        if User.query.filter_by(username=value).first():
            raise ValidationError('Username already exists')
    
    @validates('email')
    def validate_email_field(self, value: str, **kwargs: Any) -> None:
        if not validate_email(value):
            raise ValidationError('Invalid email format')
        
        if User.query.filter_by(email=value).first():
            raise ValidationError('Email already exists')
    
    @validates('password')
    def validate_password_field(self, value: str, **kwargs: Any) -> None:
        is_valid, error = validate_password_strength(value)
        if not is_valid:
            raise ValidationError(error or "Invalid password")
    
    @validates('phone_number')
    def validate_phone_field(self, value: str | None, **kwargs: Any) -> None:
        if value and not validate_phone_number(value):
            raise ValidationError('Invalid phone number format. Use international format (e.g., +1234567890)')
    
    @validates_schema
    def validate_passwords_match(self, data: dict[str, Any], **kwargs: Any) -> None:
        if 'password' in data and 'confirm_password' in data:
            if data['password'] != data['confirm_password']:
                raise ValidationError(
                    {'confirmPassword': ['Passwords do not match']},
                )
