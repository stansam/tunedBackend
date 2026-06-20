from marshmallow import Schema, fields, validate, post_load
from tuned.models.enums import OrderStatus, RevisionRequestStatus, Priority
from tuned.dtos.order import OrderListRequestDTO


class AdminOrderListRequestSchema(Schema):
    """Reuses the existing OrderListRequestDTO — admin version has no client_id filter."""
    status    = fields.String(required=False, allow_none=True,
                              validate=validate.OneOf([e.value for e in OrderStatus]))
    service_id = fields.String(required=False, allow_none=True)
    academic_level_id = fields.String(required=False, allow_none=True)
    q         = fields.String(required=False, allow_none=True)
    page      = fields.Integer(required=False, validate=validate.Range(min=1), load_default=1)
    per_page  = fields.Integer(required=False, validate=validate.Range(min=1, max=100), load_default=10)
    sort      = fields.String(required=False, allow_none=True)
    order     = fields.String(required=False, allow_none=True)

    @post_load
    def make_dto(self, data, **kwargs):
        return OrderListRequestDTO(**data)


class AdminUpdateRevisionStatusSchema(Schema):
    status = fields.String(
        required=True,
        validate=validate.OneOf([
            RevisionRequestStatus.IN_PROGRESS.value,
            RevisionRequestStatus.COMPLETED.value,
            RevisionRequestStatus.REJECTED.value,
            RevisionRequestStatus.CANCELLED.value,
        ])
    )
    internal_notes = fields.String(required=False, allow_none=True)


class AdminRequestDeadlineExtensionSchema(Schema):
    requested_hours = fields.Integer(required=True, validate=validate.Range(min=1, max=720))
    reason = fields.String(required=True, validate=validate.Length(min=10, max=2000))
    priority = fields.String(
        required=False,
        load_default=Priority.NORMAL.value,
        validate=validate.OneOf([e.value for e in Priority])
    )
