from marshmallow import Schema, fields, validate

class BulkDownloadSchema(Schema):
    asset_ids = fields.List(
        fields.String(required=True),
        required=True,
        validate=validate.Length(min=1)
    )
