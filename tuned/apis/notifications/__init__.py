from flask import Blueprint

def init_app(app):
    from .routes.routes import bp
    app.register_blueprint(bp, url_prefix='/api/notifications')
