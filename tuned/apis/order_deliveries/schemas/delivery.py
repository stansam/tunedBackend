from marshmallow import Schema, fields, validate
from tuned.models.enums import DeliveryStatus

class UpdateOrderDeliveryStatusSchema(Schema):
    delivery_status = fields.Str(
        required=True, 
        validate=validate.OneOf([e.value for e in DeliveryStatus])
    )
