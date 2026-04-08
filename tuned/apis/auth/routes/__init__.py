from tuned.apis.auth.routes.auth import AuthCheck, Login, Logout

ROUTES = [
    {'url_rule': '/auth/me', 'view_func': AuthCheck.as_view('auth_check'), 'methods': ['GET']},
    {'url_rule': '/auth/login', 'view_func': Login.as_view('login'), 'methods': ['POST']},
    {'url_rule': '/auth/logout', 'view_func': Logout.as_view('logout'), 'methods': ['POST']}
]