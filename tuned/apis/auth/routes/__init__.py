from tuned.apis.auth.routes.auth import AuthCheck, Login

ROUTES = [
    {'url_rule': '/auth/me', 'view_func': AuthCheck.as_view('auth_check'), 'methods': ['GET']},
    {'url_rule': '/auth/login', 'view_func': Login.as_view('login'), 'methods': ['POST']}
]