from marshmallow import Schema, fields, validate, validates, ValidationError
import uuid

class CheckoutSchema(Schema):
    order_id = fields.String(required=True, validate=validate.Length(min=1))
    payment_method_id = fields.String(required=True, validate=validate.Length(min=1))
    client_proof_reference = fields.String(
        required=False,
        allow_none=True,
        validate=[
            validate.Length(min=3, max=255),
            validate.Regexp(r"^[a-zA-Z0-9\-_/]+$", error="Reference must only contain alphanumeric characters, hyphens, underscores, or slashes.")
        ]
    )

    @validates("order_id")
    def validate_order_id_uuid(self, value: str, **kwargs) -> None:
        try:
            uuid.UUID(value)
        except ValueError:
            raise ValidationError("order_id must be a valid UUID string.")

    @validates("payment_method_id")
    def validate_payment_method_id_uuid(self, value: str, **kwargs) -> None:
        try:
            uuid.UUID(value)
        except ValueError:
            raise ValidationError("payment_method_id must be a valid UUID string.")

class AdminVerifySchema(Schema):
    admin_notes = fields.String(required=False, allow_none=True)

class AdminRejectSchema(Schema):
    rejection_reason = fields.String(required=True, validate=validate.Length(min=1, max=1000))
