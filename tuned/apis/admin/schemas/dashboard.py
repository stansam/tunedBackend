from marshmallow import Schema, fields

class SpendingVelocitySchema(Schema):
    month  = fields.String()
    amount = fields.Float()

class ChartDataSchema(Schema):
    name  = fields.String()
    value = fields.Integer()

class AdminKPIResponseSchema(Schema):
    active_orders   = fields.Integer()
    total_revenue   = fields.Float()
    total_clients   = fields.Integer()
    pending_actions = fields.Integer()

class AdminAnalyticsResponseSchema(Schema):
    spending_velocity = fields.List(fields.Nested(SpendingVelocitySchema))
    project_lifecycle = fields.List(fields.Nested(ChartDataSchema))
    service_mix       = fields.List(fields.Nested(ChartDataSchema))
    referral_growth   = fields.List(fields.Nested(ChartDataSchema))

class UpcomingDeadlineSchema(Schema):
    id           = fields.String()
    order_number = fields.String()
    title        = fields.String(allow_none=True)
    due_date     = fields.String()
    priority     = fields.String()

class ActivityFeedSchema(Schema):
    id          = fields.String()
    action      = fields.String()
    entity_type = fields.String()
    entity_id   = fields.String()
    created_at  = fields.String()

class AdminTrackingResponseSchema(Schema):
    upcoming_deadlines = fields.List(fields.Nested(UpcomingDeadlineSchema))
    activity_feed      = fields.List(fields.Nested(ActivityFeedSchema))

class AlertSchema(Schema):
    id         = fields.String()
    type       = fields.String()
    message    = fields.String()
    metadata   = fields.Dict(keys=fields.String(), values=fields.String())
    created_at = fields.String()

class AdminAlertsResponseSchema(Schema):
    alerts = fields.List(fields.Nested(AlertSchema))
