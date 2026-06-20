from marshmallow import Schema, fields

class AdminNavStatsResponseSchema(Schema):
    active_orders_count = fields.Integer(required=True)
    payments_count      = fields.Integer(required=True)
    chat_count          = fields.Integer(required=True)
    testimonials_count  = fields.Integer(required=True)
