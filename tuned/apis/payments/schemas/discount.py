from marshmallow import Schema, fields, validate

class ValidateCheckoutDiscountSchema(Schema):
    """
    Validates discount code at checkout time (dry-run).
    """
    code = fields.String(required=True, validate=validate.Length(min=1, max=20))
    order_total = fields.Float(required=True, validate=validate.Range(min=0.01))
