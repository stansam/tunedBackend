from marshmallow import Schema, fields, validate

class AdminSampleSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    content = fields.Str(required=True)
    excerpt = fields.Str(load_default="")
    service_id = fields.Str(required=True)
    word_count = fields.Int(load_default=0)
    featured = fields.Bool(load_default=False)
    image = fields.Str(load_default="")
    slug = fields.Str(validate=validate.Length(min=1, max=200))
    tags = fields.List(fields.Str(), load_default=list)

class AdminSampleUpdateSchema(Schema):
    title = fields.Str(validate=validate.Length(min=1, max=200))
    content = fields.Str()
    excerpt = fields.Str()
    service_id = fields.Str()
    word_count = fields.Int()
    featured = fields.Bool()
    image = fields.Str()
    slug = fields.Str(validate=validate.Length(min=1, max=200))
    tags = fields.List(fields.Str())
