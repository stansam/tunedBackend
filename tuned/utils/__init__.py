"""
Global utilities package.

Exports commonly used utility functions for the entire application.
"""
from tuned.utils.responses import (
    success_response,
    error_response,
    validation_error_response,
    paginated_response,
    created_response,
    no_content_response,
    unauthorized_response,
    forbidden_response,
    not_found_response
)

from tuned.utils.tokens import (
    generate_token,
    verify_token,
    generate_verification_token,
    verify_verification_token,
    generate_password_reset_token,
    verify_password_reset_token,
    generate_referral_code,
    generate_secure_random_string
)

from tuned.utils.validators import (
    validate_email,
    validate_password_strength,
    validate_phone_number,
    validate_username,
    validate_url,
    validate_integer,
    sanitize_string
)

from tuned.utils.email import (
    send_email,
    send_async_email,
    send_bulk_emails,
    send_test_email
)

from tuned.utils.decorators import (
    rate_limit,
    log_activity,
    require_api_key,
    cors_preflight
)


__all__ = [
    # Response utilities
    'success_response',
    'error_response',
    'validation_error_response',
    'paginated_response',
    'created_response',
    'no_content_response',
    'unauthorized_response',
    'forbidden_response',
    'not_found_response',
    
    # Token utilities
    'generate_token',
    'verify_token',
    'generate_verification_token',
    'verify_verification_token',
    'generate_password_reset_token',
    'verify_password_reset_token',
    'generate_referral_code',
    'generate_secure_random_string',
    
    # Validation utilities
    'validate_email',
    'validate_password_strength',
    'validate_phone_number',
    'validate_username',
    'validate_url',
    'validate_integer',
    'sanitize_string',
    
    # Email utilities
    'send_email',
    'send_async_email',
    'send_bulk_emails',
    'send_test_email',
    
    # Decorators
    'rate_limit',
    'log_activity',
    'require_api_key',
    'cors_preflight',
]
