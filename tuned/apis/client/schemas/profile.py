from marshmallow import Schema, fields, validate, ValidationError, validates_schema

class UpdateProfileSchema(Schema):
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    phone_number = fields.Str(allow_none=True, validate=validate.Length(max=20))
    gender = fields.Str(allow_none=True, validate=validate.OneOf(["male", "female", "unknown"]))

class ChangePasswordSchema(Schema):
    current_password = fields.Str(required=True, validate=validate.Length(min=1))
    new_password = fields.Str(required=True, validate=validate.Length(min=8))
    confirm_password = fields.Str(required=True, validate=validate.Length(min=8))

    @validates_schema
    def validate_password_match(self, data, **kwargs):
        if data.get("new_password") != data.get("confirm_password"):
            raise ValidationError("Passwords do not match", field_name="confirm_password")
