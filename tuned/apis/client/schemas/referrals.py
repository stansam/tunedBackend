from marshmallow import Schema, fields, validate

class ReferralFilterSchema(Schema):
    page = fields.Int(missing=1, validate=validate.Range(min=1))
    per_page = fields.Int(missing=10, validate=validate.Range(min=1, max=100))
    status = fields.Str(validate=validate.OneOf(['PENDING', 'COMPLETED', 'ACTIVE']), required=False)

class RedeemRewardSchema(Schema):
    points = fields.Int(required=True, validate=validate.Range(min=10))
    order_id = fields.Str(required=True)

class ReferralShareSchema(Schema):
    platform = fields.Str(required=True, validate=validate.OneOf(['facebook', 'twitter', 'linkedin', 'whatsapp', 'email', 'copy_link']))
    message = fields.Str(required=False)
