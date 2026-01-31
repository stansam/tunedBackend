"""
Validation schemas for blog-related endpoints.

Includes schemas for:
- Blog filtering and pagination
- Blog comment creation
- Blog comment reactions
"""
from marshmallow import Schema, fields, validate, validates, ValidationError


class BlogFilterSchema(Schema):
    """Schema for filtering and paginating blog posts."""
    
    category_id = fields.Int(
        required=False,
        validate=validate.Range(min=1),
        error_messages={
            'invalid': 'Category ID must be an integer',
            'validator_failed': 'Category ID must be at least 1'
        }
    )
    
    is_published = fields.Bool(
        required=False,
        load_default=True,
        error_messages={
            'invalid': 'Published status must be a boolean value'
        }
    )
    
    q = fields.Str(
        required=False,
        validate=validate.Length(min=2, max=200),
        error_messages={
            'invalid': 'Search query must be a string',
            'min': 'Search query must be at least 2 characters',
            'max': 'Search query must not exceed 200 characters'
        }
    )
    
    sort = fields.Str(
        required=False,
        validate=validate.OneOf(['published_at', 'created_at', 'title']),
        load_default='published_at',
        error_messages={
            'invalid': 'Sort field must be a string',
            'validator_failed': 'Sort must be one of: published_at, created_at, title'
        }
    )
    
    order = fields.Str(
        required=False,
        validate=validate.OneOf(['asc', 'desc']),
        load_default='desc',
        error_messages={
            'invalid': 'Order must be a string',
            'validator_failed': 'Order must be either asc or desc'
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


class BlogCommentSchema(Schema):
    """Schema for creating blog comments."""
    
    content = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=5000),
        error_messages={
            'required': 'Comment content is required',
            'invalid': 'Comment content must be a string',
            'min': 'Comment must be at least 3 characters',
            'max': 'Comment must not exceed 5000 characters'
        }
    )
    
    # For guest comments (optional if authenticated)
    name = fields.Str(
        required=False,
        validate=validate.Length(max=100),
        error_messages={
            'invalid': 'Name must be a string',
            'max': 'Name must not exceed 100 characters'
        }
    )
    
    email = fields.Email(
        required=False,
        error_messages={
            'invalid': 'Invalid email address format'
        }
    )
    
    @validates('content')
    def validate_content(self, value):
        """Validate comment content for spam patterns."""
        # Check for excessive links
        if value.count('http://') + value.count('https://') > 2:
            raise ValidationError('Comments cannot contain more than 2 links')
        
        # Check for excessive repetition
        words = value.lower().split()
        if len(words) > 5:
            unique_words = set(words)
            if len(unique_words) / len(words) < 0.3:
                raise ValidationError('Comment appears to be spam')


class CommentReactionSchema(Schema):
    """Schema for blog comment reactions (likes/dislikes)."""
    
    reaction_type = fields.Str(
        required=True,
        validate=validate.OneOf(['like', 'dislike']),
        error_messages={
            'required': 'Reaction type is required',
            'invalid': 'Reaction type must be a string',
            'validator_failed': 'Reaction type must be either like or dislike'
        }
    )
