from marshmallow import Schema, fields, validate, post_load
from tuned.models.enums import FormatStyle, LineSpacing, ReportType
from tuned.dtos.order import CreateOrderRequestDTO, ValidateDiscountRequestDTO, OrderDraftCreateDTO

class CreateOrderSchema(Schema):
    service_id = fields.String(required=True)
    academic_level_id = fields.String(required=True)
    deadline_id = fields.String(required=True)
    title = fields.String(required=True, validate=validate.Length(min=1))
    description = fields.String(required=True, validate=validate.Length(min=1))
    word_count = fields.Integer(required=True, validate=validate.Range(min=1))
    page_count = fields.Float(required=True, validate=validate.Range(min=0.1))
    format_style = fields.String(required=True, validate=validate.OneOf([e.value for e in FormatStyle]))
    sources = fields.Integer(required=True, validate=validate.Range(min=0))
    line_spacing = fields.String(required=True, validate=validate.OneOf([e.value for e in LineSpacing]))
    instructions = fields.String(required=False, allow_none=True)
    report_type = fields.String(required=False, allow_none=True, validate=validate.OneOf([e.value for e in ReportType]))
    discount_code = fields.String(required=False, allow_none=True)
    points_to_redeem = fields.Integer(required=False, load_default=0)

    @post_load
    def make_dto(self, data, **kwargs):
        return CreateOrderRequestDTO(**data)

class ValidateDiscountSchema(Schema):
    code = fields.String(required=True)
    subtotal = fields.Float(required=True, validate=validate.Range(min=0.0))

    @post_load
    def make_dto(self, data, **kwargs):
        return ValidateDiscountRequestDTO(**data)

class SaveDraftSchema(Schema):
    service_id = fields.String(required=False, allow_none=True)
    academic_level_id = fields.String(required=False, allow_none=True)
    deadline_id = fields.String(required=False, allow_none=True)
    title = fields.String(required=False, allow_none=True)
    description = fields.String(required=False, allow_none=True)
    word_count = fields.Integer(required=False, allow_none=True)
    page_count = fields.Float(required=False, allow_none=True)
    format_style = fields.String(required=False, allow_none=True, validate=validate.OneOf([e.value for e in FormatStyle]))
    sources = fields.Integer(required=False, allow_none=True)
    line_spacing = fields.String(required=False, allow_none=True, validate=validate.OneOf([e.value for e in LineSpacing]))
    report_type = fields.String(required=False, allow_none=True, validate=validate.OneOf([e.value for e in ReportType]))
    discount_code = fields.String(required=False, allow_none=True)
    points_to_redeem = fields.Integer(required=False, load_default=0)

    @post_load
    def make_dto(self, data, **kwargs):
        return OrderDraftCreateDTO(user_id="", **data)
