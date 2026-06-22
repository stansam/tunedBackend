from marshmallow import Schema, fields, validate

class TrackSearchEventSchema(Schema):
    query = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    search_type = fields.Str(required=False, load_default='all')
    session_key = fields.Str(required=False, allow_none=True)
    result_count = fields.Int(required=False, load_default=0)
    device_type = fields.Str(required=False, allow_none=True)
    source = fields.Str(required=False, load_default='hero')

class TrackSearchClickSchema(Schema):
    event_id = fields.Str(required=True)
    clicked_type = fields.Str(required=True, validate=validate.OneOf(['service', 'sample', 'blog', 'faq', 'tag']))
    clicked_id = fields.Str(required=True)
    position = fields.Int(required=True, validate=validate.Range(min=0))
