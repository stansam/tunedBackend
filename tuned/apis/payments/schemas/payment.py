from marshmallow import Schema, fields, validate

class CheckoutSchema(Schema):
    order_id = fields.String(required=True, validate=validate.Length(min=1))
    payment_method_id = fields.String(required=True, validate=validate.Length(min=1))
    client_proof_reference = fields.String(required=False, allow_none=True)

class AdminVerifySchema(Schema):
    admin_notes = fields.String(required=False, allow_none=True)

class AdminRejectSchema(Schema):
    rejection_reason = fields.String(required=True, validate=validate.Length(min=1, max=1000))
