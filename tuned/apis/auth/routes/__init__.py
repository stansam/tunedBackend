from tuned.apis.auth.routes.auth import AuthCheck, Login, Logout, Register
from tuned.apis.auth.routes.email_verification import (
    EmailVerificationResend,
    EmailVerifyConfirm,
)

ROUTES = [
    # Auth
    {'url_rule': '/auth/me',     'view_func': AuthCheck.as_view('auth_check'), 'methods': ['GET']},
    {'url_rule': '/auth/login',  'view_func': Login.as_view('login'),          'methods': ['POST']},
    {'url_rule': '/auth/logout', 'view_func': Logout.as_view('logout'),        'methods': ['POST']},
    {'url_rule': '/auth/register', 'view_func': Register.as_view('register'),  'methods': ['POST']},
    # Email verification
    {
        'url_rule': '/auth/email/verify/resend',
        'view_func': EmailVerificationResend.as_view('email_verify_resend'),
        'methods': ['POST'],
    },
    {
        'url_rule': '/auth/email/verify/confirm',
        'view_func': EmailVerifyConfirm.as_view('email_verify_confirm'),
        'methods': ['GET'],
    },
]