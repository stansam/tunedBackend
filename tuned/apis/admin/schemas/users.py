from marshmallow import Schema, fields, validate, post_load
from tuned.dtos.admin.users import AdminUserListRequestDTO

class AdminUserListRequestSchema(Schema):
    status   = fields.String(required=False, allow_none=True,
                             validate=validate.OneOf(["active", "dormant"]))
    clv_status = fields.String(required=False, allow_none=True,
                               validate=validate.OneOf(["high", "medium", "low", "normal"]))
    q        = fields.String(required=False, allow_none=True)
    sort     = fields.String(required=False, allow_none=True,
                             validate=validate.OneOf(["created_at", "total_spent", "orders_count", "name", "last_order_at"]))
    order    = fields.String(required=False, allow_none=True,
                             validate=validate.OneOf(["asc", "desc"]))
    page     = fields.Integer(required=False, load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(required=False, load_default=5, validate=validate.Range(min=1, max=50))

    @post_load
    def make_dto(self, data, **kwargs):
        return AdminUserListRequestDTO(**data)


class BroadcastMessageSchema(Schema):
    message = fields.String(required=True, validate=validate.Length(min=1, max=500))


class DirectMessageSchema(Schema):
    message = fields.String(required=True, validate=validate.Length(min=1, max=500))
