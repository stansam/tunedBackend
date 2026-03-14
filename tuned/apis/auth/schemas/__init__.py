"""
Auth schemas package.

Exports all authentication validation schemas.
"""
from tuned.auth.schemas.registration import RegistrationSchema
from tuned.auth.schemas.login import LoginSchema
from tuned.auth.schemas.password_reset import PasswordResetRequestSchema, PasswordResetConfirmSchema
from tuned.auth.schemas.email_verification import EmailVerificationSchema
from tuned.auth.schemas.resend_verification import ResendVerificationSchema



__all__ = [
    'RegistrationSchema',
    'LoginSchema',
    'PasswordResetRequestSchema',
    'PasswordResetConfirmSchema',
    'EmailVerificationSchema',
    'ResendVerificationSchema',
]

"""
Marshmallow validation schemas for authentication endpoints.

NOTE: Marshmallow 3.23+ passes additional kwargs like 'data_key' to validator methods.
All @validates methods must accept **kwargs even if not used.
"""