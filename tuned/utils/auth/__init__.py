"""
Auth utilities package.

Exports auth-specific utility functions.
"""
from tuned.utils.auth.password import (
    hash_password,
    verify_password,
    check_password_strength,
    generate_temporary_password,
    rehash_password_if_needed
)

from tuned.utils.auth.helpers import (
    get_current_user,
    check_account_lockout,
    record_login_attempt,
    get_user_ip,
    get_user_agent,
    is_email_verified_required,
    get_user_by_email_or_username
)

from tuned.utils.auth.decorators import (
    jwt_required_fresh,
    admin_required,
    verified_email_required,
    active_user_required,
    combined_auth_check
)


__all__ = [
    # Password utilities
    'hash_password',
    'verify_password',
    'check_password_strength',
    'generate_temporary_password',
    'rehash_password_if_needed',
    
    # Helper functions
    'get_current_user',
    'check_account_lockout',
    'record_login_attempt',
    'get_user_ip',
    'get_user_agent',
    'is_email_verified_required',
    'get_user_by_email_or_username',
    
    # Decorators
    'jwt_required_fresh',
    'admin_required',
    'verified_email_required',
    'active_user_required',
    'combined_auth_check',
]
