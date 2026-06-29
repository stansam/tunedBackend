from marshmallow import Schema, fields, validate, post_load
from tuned.models.enums import PaymentStatus
from tuned.dtos.payment import AdminPaymentListRequestDTO

class AdminPaymentListRequestSchema(Schema):
    status = fields.String(
        required=False,
        allow_none=True,
        validate=validate.OneOf([e.value for e in PaymentStatus])
    )
    q = fields.String(required=False, allow_none=True)
    page = fields.Integer(required=False, validate=validate.Range(min=1), load_default=1)
    per_page = fields.Integer(required=False, validate=validate.Range(min=1, max=100), load_default=10)

    @post_load
    def make_dto(self, data, **kwargs):
        return AdminPaymentListRequestDTO(**data)

class AdminPaymentResponseSchema(Schema):
    id = fields.String()
    payment_id = fields.String()
    order_id = fields.String()
    user_id = fields.String()
    amount = fields.Float()
    status = fields.String()
    accepted_method_id = fields.String()
    currency = fields.String()
    client_proof_reference = fields.String(allow_none=True)
    pesapal_tracking_id = fields.String(allow_none=True)
    admin_notes = fields.String(allow_none=True)
    client_marked_paid_at = fields.DateTime(allow_none=True)
    admin_verified_at = fields.DateTime(allow_none=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    client_name = fields.String(allow_none=True)
    client_email = fields.String(allow_none=True)
    order_number = fields.String(allow_none=True)
    payment_method_name = fields.String(allow_none=True)
    payment_method_category = fields.String(allow_none=True)

class AdminPaymentListResponseSchema(Schema):
    payments = fields.Nested(AdminPaymentResponseSchema, many=True)
    total = fields.Integer()
    page = fields.Integer()
    per_page = fields.Integer()
