"""
Marshmallow validation schemas for authentication endpoints.

Provides comprehensive validation schemas for:
- User registration
- Login
- Password reset (request and confirm)
- Email verification
- Email change

All schemas include field-level validation, custom validators,
and helpful error messages.
"""
from marshmallow import Schema, fields, validates, validates_schema, ValidationError, post_load
from tuned.models.user import User, GenderEnum
from tuned.utils.validators import validate_email, validate_password_strength, validate_username, validate_phone_number


class RegistrationSchema(Schema):
    """
    Schema for user registration.
    
    Required fields:
    - username: 3-64 characters, alphanumeric with underscores/hyphens
    - email: Valid email format, must be unique
    - password: Must meet strength requirements
    - confirm_password: Must match password
    - first_name: User's first name
    - last_name: User's last name
    - gender: 'male' or 'female'
    
    Optional fields:
    - phone_number: International format (E.164)
    """
    username = fields.Str(required=True)
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)
    confirm_password = fields.Str(required=True, load_only=True)
    first_name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    gender = fields.Str(required=True)
    phone_number = fields.Str(required=False, allow_none=True)
    
    @validates('username')
    def validate_username_field(self, value):
        """Validate username format and uniqueness."""
        # Check format
        is_valid, error = validate_username(value)
        if not is_valid:
            raise ValidationError(error)
        
        # Check uniqueness
        if User.query.filter_by(username=value).first():
            raise ValidationError('Username already exists')
    
    @validates('email')
    def validate_email_field(self, value):
        """Validate email format and uniqueness."""
        # Check format
        if not validate_email(value):
            raise ValidationError('Invalid email format')
        
        # Check uniqueness
        if User.query.filter_by(email=value).first():
            raise ValidationError('Email already exists')
    
    @validates('password')
    def validate_password_field(self, value):
        """Validate password strength."""
        is_valid, error = validate_password_strength(value)
        if not is_valid:
            raise ValidationError(error)
    
    @validates('gender')
    def validate_gender_field(self, value):
        """Validate gender value."""
        valid_genders = ['male', 'female']
        if value.lower() not in valid_genders:
            raise ValidationError('Gender must be either "male" or "female"')
    
    @validates('phone_number')
    def validate_phone_field(self, value):
        """Validate phone number format if provided."""
        if value and not validate_phone_number(value):
            raise ValidationError('Invalid phone number format. Use international format (e.g., +1234567890)')
    
    @validates_schema
    def validate_passwords_match(self, data, **kwargs):
        """Validate that password and confirm_password match."""
        if data.get('password') != data.get('confirm_password'):
            raise ValidationError({'confirm_password': ['Passwords do not match']})


class LoginSchema(Schema):
    """
    Schema for user login.
    
    Fields:
    - email: Email address or username
    - password: User password
    - remember_me: Optional, extend session duration
    """
    email = fields.Str(required=True)  # Can be email or username
    password = fields.Str(required=True, load_only=True)
    remember_me = fields.Bool(load_default=False)
    
    @validates('email')
    def validate_email_field(self, value):
        """Basic validation - ensure not empty."""
        if not value or not value.strip():
            raise ValidationError('Email or username is required')
    
    @validates('password')
    def validate_password_field(self, value):
        """Basic validation - ensure not empty."""
        if not value:
            raise ValidationError('Password is required')


class PasswordResetRequestSchema(Schema):
    """
    Schema for password reset request.
    
    Fields:
    - email: User's email address
    """
    email = fields.Email(required=True)
    
    @validates('email')
    def validate_email_field(self, value):
        """Validate email format."""
        if not validate_email(value):
            raise ValidationError('Invalid email format')
        # Note: Don't check if email exists (security - don't reveal user existence)


class PasswordResetConfirmSchema(Schema):
    """
    Schema for password reset confirmation.
    
    Fields:
    - token: Reset token from email
    - new_password: New password
    - confirm_password: Password confirmation
    """
    token = fields.Str(required=True)
    new_password = fields.Str(required=True, load_only=True)
    confirm_password = fields.Str(required=True, load_only=True)
    
    @validates('token')
    def validate_token_field(self, value):
        """Basic token validation."""
        if not value or not value.strip():
            raise ValidationError('Reset token is required')
    
    @validates('new_password')
    def validate_password_field(self, value):
        """Validate new password strength."""
        is_valid, error = validate_password_strength(value)
        if not is_valid:
            raise ValidationError(error)
    
    @validates_schema
    def validate_passwords_match(self, data, **kwargs):
        """Validate that passwords match."""
        if data.get('new_password') != data.get('confirm_password'):
            raise ValidationError({'confirm_password': ['Passwords do not match']})


class EmailVerificationSchema(Schema):
    """
    Schema for email verification.
    
    Fields:
    - token: Verification token from email
    """
    token = fields.Str(required=True)
    
    @validates('token')
    def validate_token_field(self, value):
        """Basic token validation."""
        if not value or not value.strip():
            raise ValidationError('Verification token is required')


class ResendVerificationSchema(Schema):
    """
    Schema for resending verification email.
    
    Fields:
    - email: User's email address
    """
    email = fields.Email(required=True)
    
    @validates('email')
    def validate_email_field(self, value):
        """Validate email format."""
        if not validate_email(value):
            raise ValidationError('Invalid email format')


class ChangeEmailSchema(Schema):
    """
    Schema for changing user email.
    
    Fields:
    - new_email: New email address
    - password: Current password for verification
    """
    new_email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)
    
    @validates('new_email')
    def validate_new_email_field(self, value):
        """Validate new email format and uniqueness."""
        if not validate_email(value):
            raise ValidationError('Invalid email format')
        
        # Check if email is already in use
        if User.query.filter_by(email=value).first():
            raise ValidationError('Email already in use')
    
    @validates('password')
    def validate_password_field(self, value):
        """Ensure password is provided."""
        if not value:
            raise ValidationError('Password is required to change email')


class ChangePasswordSchema(Schema):
    """
    Schema for changing user password.
    
    Fields:
    - current_password: Current password for verification
    - new_password: New password
    - confirm_password: Password confirmation
    """
    current_password = fields.Str(required=True, load_only=True)
    new_password = fields.Str(required=True, load_only=True)
    confirm_password = fields.Str(required=True, load_only=True)
    
    @validates('current_password')
    def validate_current_password_field(self, value):
        """Ensure current password is provided."""
        if not value:
            raise ValidationError('Current password is required')
    
    @validates('new_password')
    def validate_new_password_field(self, value):
        """Validate new password strength."""
        is_valid, error = validate_password_strength(value)
        if not is_valid:
            raise ValidationError(error)
    
    @validates_schema
    def validate_passwords_match(self, data, **kwargs):
        """Validate that new passwords match."""
        if data.get('new_password') != data.get('confirm_password'):
            raise ValidationError({'confirm_password': ['Passwords do not match']})
        
        # Ensure new password is different from current
        if data.get('current_password') == data.get('new_password'):
            raise ValidationError({'new_password': ['New password must be different from current password']})
