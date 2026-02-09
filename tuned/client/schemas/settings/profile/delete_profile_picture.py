from marshmallow import Schema, fields, validate, post_load

class DeleteProfilePictureSchema(Schema):
    """Validation schema for deleting profile picture."""
    
    confirm = fields.Boolean(
        required=True,
        validate=validate.Equal(True, error='Confirmation required')
    )