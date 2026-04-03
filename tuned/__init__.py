import os
import logging
from flask import Flask
from tuned.core.config import config
from tuned.core.logging import _configure_logging

def create_app(config_name=None):
    app = Flask(__name__)
    
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    _configure_logging(config[config_name])
    logger = logging.getLogger(__name__)
    logger.info(
        "Creating Flask app [env=%s version=%s]",
        config[config_name].FLASK_ENV,
        config[config_name].APP_VERSION,
    )

    app.config.from_object(config[config_name])
    
    from tuned.extensions import db, migrate, login_manager, jwt, cors, socketio, mail
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    
    cors_origins = app.config.get('CORS_ORIGINS', '*')
    cors.init_app(app, origins=cors_origins, supports_credentials=True)
    
    socketio_kwargs = {
        'cors_allowed_origins': cors_origins,
        'async_mode': 'eventlet',
        'logger': app.config.get('DEBUG', False),
        'engineio_logger': app.config.get('DEBUG', False)
    }
    if app.config.get('SOCKETIO_MESSAGE_QUEUE'):
        socketio_kwargs['message_queue'] = app.config['SOCKETIO_MESSAGE_QUEUE']
    
    socketio.init_app(app, **socketio_kwargs)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.session_protection = 'strong'
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID for Flask-Login."""
        from tuned.models.user import User
        return User.query.get(int(user_id))
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        """Check if JWT token is blacklisted (logout functionality)."""
        from tuned.redis_client import is_token_blacklisted
        jti = jwt_payload['jti']
        return is_token_blacklisted(jti)
    
    from tuned.apis import(
        main_bp
        # , auth_bp, client_bp, admin_bp 
    ) 
    from tuned.manage import manage_bp
    
    # app.register_blueprint(admin_bp, url_prefix='/api/admin')
    # app.register_blueprint(auth_bp, url_prefix='/api/auth')
    # app.register_blueprint(client_bp, url_prefix='/api/client')
    app.register_blueprint(manage_bp)
    
    # from tuned.apis.client.routes.settings.preferences import preferences_bp
    # app.register_blueprint(preferences_bp, url_prefix='/client/settings/preferences')
    
    app.register_blueprint(main_bp, url_prefix="/api")  # No prefix - root routes

    
    if app.config.get('PROXY_FIX'):
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=1,      # Trust X-Forwarded-For
            x_proto=1,    # Trust X-Forwarded-Proto
            x_host=1,     # Trust X-Forwarded-Host
            x_prefix=1    # Trust X-Forwarded-Prefix
        )
    
    register_error_handlers(app)
    
    register_shell_context(app)

    return app


def register_error_handlers(app):
    """Register error handlers for common HTTP errors."""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from tuned.extensions import db
        db.session.rollback()
        return {'error': 'Internal server error'}, 500


def register_shell_context(app):
    """Register shell context for flask shell command."""
    
    @app.shell_context_processor
    def make_shell_context():
        from tuned.extensions import db
        from tuned import models
        return {
            'db': db,
            'models': models,
        }
