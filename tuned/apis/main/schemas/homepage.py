from marshmallow import Schema, fields, validate, validates, ValidationError
import re


from typing import Any

class NewsletterSubscribeSchema(Schema):
    email = fields.Email(
        required=True,
        error_messages={
            'required': 'Email address is required',
            'invalid': 'Invalid email address format'
        }
    )
    
    name = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
        error_messages={
            'invalid': 'Name must be a string',
            'max': 'Name must not exceed 100 characters'
        }
    )
    
    @validates('email')
    def validate_email(self, value: str, **kwargs: Any) -> str:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise ValidationError('Invalid email address format')
        
        disposable_domains = ['tempmail.com', 'throwaway.email', '10minutemail.com']
        domain = value.split('@')[1].lower()
        if domain in disposable_domains:
            raise ValidationError('Disposable email addresses are not allowed')
        
        return value


class SearchQuerySchema(Schema):
    q = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=200),
        error_messages={
            'required': 'Search query is required',
            'invalid': 'Search query must be a string',
            'min': 'Search query must be at least 2 characters',
            'max': 'Search query must not exceed 200 characters'
        }
    )
    
    type = fields.Str(
        required=False,
        validate=validate.OneOf([
            'all', 'service', 'sample', 'blog', 'faq', 'tag'
        ]),
        error_messages={
            'invalid': 'Invalid search type',
            'validator_failed': 'Search type must be one of: all, service, sample, blog, faq, tag'
        }
    )
    
    page = fields.Int(
        required=False,
        validate=validate.Range(min=1),
        load_default=1,
        error_messages={
            'invalid': 'Page must be an integer',
            'validator_failed': 'Page must be at least 1'
        }
    )
    
    per_page = fields.Int(
        required=False,
        validate=validate.Range(min=1, max=100),
        load_default=20,
        error_messages={
            'invalid': 'Items per page must be an integer',
            'validator_failed': 'Items per page must be between 1 and 100'
        }
    )

class CalculatePriceSchema(Schema):
    service_id = fields.Str(
        required=True,
        error_messages={
            'required': 'Service ID is required',
            'invalid': 'Service ID must be a string',
        }
    )
    
    level_id = fields.Str(
        required=True,
        error_messages={
            'required': 'Level ID is required',
            'invalid': 'Level ID must be a string',
        }
    )

    deadline = fields.AwareDateTime(
        required=True,
        error_messages={
            'required': 'Deadline is required',
            'invalid': 'Deadline must be a datetime',
        }
    )
    
    word_count = fields.Int(
        required=True,
        error_messages={
            'required': 'Word count is required',
            'invalid': 'Word count must be an integer',
        }
    )

    page_count = fields.Int(
        required=True,
        error_messages={
            'required': 'Page count is required',
            'invalid': 'Page count must be an integer',
        }
    )

    report_type = fields.Str(
        required=False,
        validate=validate.OneOf([
            'standard', 'turnitin'
        ]),
        error_messages={
            'invalid': 'Invalid report type',
            'validator_failed': 'Report type must be one of: standard, turnitin'
        }
    )
