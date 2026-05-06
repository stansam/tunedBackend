from marshmallow import Schema, fields, validate, post_load
from tuned.models.enums import FormatStyle, LineSpacing, ReportType, OrderStatus
from tuned.dtos import CreateOrderRequestDTO, ValidateDiscountRequestDTO, OrderDraftCreateDTO, OrderListRequestDTO

class CreateOrderSchema(Schema):
    service_id = fields.String(required=True)
    level_id = fields.String(required=True)
    # deadline_id = fields.String(required=True)
    deadline = fields.AwareDateTime(required=True)
    title = fields.String(required=True, validate=validate.Length(min=1))
    instructions = fields.String(required=True, validate=validate.Length(min=1))
    word_count = fields.Integer(required=True, validate=validate.Range(min=1))
    page_count = fields.Float(required=True, validate=validate.Range(min=0.1))
    format_style = fields.String(required=True, validate=validate.OneOf([e.value for e in FormatStyle]))
    sources = fields.Integer(required=True, validate=validate.Range(min=0))
    line_spacing = fields.String(required=True, validate=validate.OneOf([e.value for e in LineSpacing]))
    # description = fields.String(required=False, allow_none=True)
    report_type = fields.String(required=False, allow_none=True, validate=validate.OneOf([e.value for e in ReportType]))
    discount_code = fields.String(required=False, allow_none=True)
    points_to_redeem = fields.Integer(required=False, load_default=0)

    @post_load
    def make_dto(self, data, **kwargs):
        return CreateOrderRequestDTO(
            service_id=data["service_id"],
            level_id=data["level_id"],
            # deadline_id="",
            title=data["title"],
            instructions=data["instructions"],
            word_count=data["word_count"],
            page_count=data["page_count"],
            format_style=FormatStyle(data["format_style"]) if data.get("format_style") else FormatStyle.APA,
            sources=data["sources"],
            line_spacing=LineSpacing(data["line_spacing"]) if data.get("line_spacing") else LineSpacing.DOUBLE,
            due_date=data["deadline"],
            report_type=ReportType(data["report_type"]) if data.get("report_type") else None,
            discount_code=data.get("discount_code"),
            points_to_redeem=data.get("points_to_redeem")
            )

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

class OrderListRequestSchema(Schema):
    status = fields.String(required=False, allow_none=True, validate=validate.OneOf([e.value for e in OrderStatus]))
    service_id = fields.String(required=False, allow_none=True)
    # deadl = fields.String(required=False, allow_none=True, validate=validate.OneOf([e.value for e in ReportType]))
    academic_level_id = fields.String(required=False, allow_none=True)
    q = fields.String(required=False, allow_none=True)
    page = fields.Integer(required=False, validate=validate.Range(min=1), load_default=1)
    per_page = fields.Integer(required=False, validate=validate.Range(min=1), load_default=10)
    
    @post_load
    def make_dto(self, data, **kwargs):
        return OrderListRequestDTO(**data)