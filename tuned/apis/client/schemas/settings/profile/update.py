from marshmallow import Schema, fields, validate, validates, post_load
from tuned.models.enums import GenderEnum

class UpdateProfileSchema(Schema):
    """Validation schema for updating user profile information."""
    
    first_name = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(min=1, max=50),
        error_messages={
            'min_length': 'First name must be at least 1 character',
            'max_length': 'First name cannot exceed 50 characters'
        }
    )
    
    last_name = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(min=1, max=50),
        error_messages={
            'min_length': 'Last name must be at least 1 character',
            'max_length': 'Last name cannot exceed 50 characters'
        }
    )
    
    phone = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Regexp(
            r'^\+?[1-9]\d{1,14}$',
            error='Invalid phone number format. Use international format (e.g., +1234567890)'
        )
    )
    
    gender = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf([g.value for g in GenderEnum])
    )
    
    date_of_birth = fields.Date(
        required=False,
        allow_none=True,
        format='%Y-%m-%d'
    )
    
    bio = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=500),
        error_messages={'max_length': 'Bio cannot exceed 500 characters'}
    )
    
    country = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100)
    )
    
    city = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100)
    )
    
    timezone = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=50)
    )
    
    @post_load
    def strip_strings(self, data, **kwargs):
        """Strip whitespace from string fields."""
        string_fields = ['first_name', 'last_name', 'bio', 'country', 'city', 'timezone']
        for field in string_fields:
            if field in data and data[field]:
                data[field] = data[field].strip()
        return data
    
    @validates('date_of_birth')
    def validate_age(self, value):
        """Ensure user is at least 13 years old."""
        from datetime import date
        
        if value:
            today = date.today()
            age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
            
            if age < 13:
                raise ValidationError('You must be at least 13 years old')
            
            if age > 120:
                raise ValidationError('Invalid date of birth')
