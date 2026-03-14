from marshmallow import Schema, fields, validate, post_load

class UpdateProfilePictureSchema(Schema):
    """Validation schema for profile picture upload."""
    
    image_format = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['jpeg', 'jpg', 'png', 'gif', 'webp'])
    )
    
    crop_data = fields.Dict(
        required=False,
        allow_none=True
    )
