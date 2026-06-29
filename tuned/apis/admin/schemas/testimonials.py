from marshmallow import Schema, fields, validate

class AdminTestimonialFilterSchema(Schema):
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Int(load_default=10, validate=validate.Range(min=1, max=100))
    status = fields.Str(load_default="all", validate=validate.OneOf(["all", "approved", "pending"]))
    service_id = fields.Str(required=False, allow_none=True)
    rating = fields.Int(required=False, allow_none=True, validate=validate.Range(min=1, max=5))
    q = fields.Str(required=False, allow_none=True)
    sort = fields.Str(load_default="created_at")
    order = fields.Str(load_default="desc", validate=validate.OneOf(["asc", "desc"]))

class AdminTestimonialUpdateSchema(Schema):
    content = fields.Str(validate=validate.Length(min=1))
    rating = fields.Int(validate=validate.Range(min=1, max=5))
    is_approved = fields.Bool()
