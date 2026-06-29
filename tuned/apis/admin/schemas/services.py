from marshmallow import Schema, fields, validate
from typing import Any
from tuned.dtos.services import ServiceResponseDTO

class AdminServiceCategorySchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(load_default="")
    order = fields.Int(load_default=0)

class AdminServiceCategoryUpdateSchema(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=100))
    description = fields.Str()
    order = fields.Int()

class AdminServiceSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(load_default="")
    category_id = fields.Str(required=True)
    pricing_category_id = fields.Str(required=True)
    featured = fields.Bool(load_default=False)
    is_active = fields.Bool(load_default=True)
    slug = fields.Str(validate=validate.Length(min=1, max=200))
    tags = fields.List(fields.Str(), load_default=list)

class AdminServiceUpdateSchema(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=100))
    description = fields.Str()
    category_id = fields.Str()
    pricing_category_id = fields.Str()
    featured = fields.Bool()
    is_active = fields.Bool()
    slug = fields.Str(validate=validate.Length(min=1, max=200))
    tags = fields.List(fields.Str())

