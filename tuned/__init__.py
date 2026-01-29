"""
Flask application factory.

This module provides the create_app() factory function that creates and
configures a Flask application instance. This pattern allows:
- Multiple app instances (e.g., for testing)
- Configuration based on environment
- No side effects on import
- Proper extension initialization order
"""
import os
from flask import Flask
from tuned.config import config


def create_app(config_name=None):
    """
    Create and configure a Flask application instance.
    
    Args:
        config_name (str): Configuration name ('development', 'testing', 'production')
                          If None, uses FLASK_ENV environment variable.
    
    Returns:
        Flask: Configured Flask application instance
    """
    # Create Flask app instance
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    from tuned.extensions import db, migrate, login_manager, jwt, cors, socketio, mail
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    
    # Configure CORS
    cors_origins = app.config.get('CORS_ORIGINS', '*')
    cors.init_app(app, origins=cors_origins, supports_credentials=True)
    
    # Configure SocketIO
    socketio_kwargs = {
        'cors_allowed_origins': cors_origins,
        'async_mode': 'eventlet',  # or 'gevent' for production
        'logger': app.config.get('DEBUG', False),
        'engineio_logger': app.config.get('DEBUG', False)
    }
    if app.config.get('SOCKETIO_MESSAGE_QUEUE'):
        socketio_kwargs['message_queue'] = app.config['SOCKETIO_MESSAGE_QUEUE']
    
    socketio.init_app(app, **socketio_kwargs)
    
    # Configure Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.session_protection = 'strong'
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID for Flask-Login."""
        from tuned.models.user import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from tuned.admin import admin_bp
    from tuned.auth import auth_bp
    from tuned.client import client_bp
    from tuned.main import main_bp
    
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(client_bp, url_prefix='/client')
    app.register_blueprint(main_bp)  # No prefix - root routes
    
    # Apply ProxyFix middleware for production deployments behind reverse proxy
    if app.config.get('PROXY_FIX'):
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=1,      # Trust X-Forwarded-For
            x_proto=1,    # Trust X-Forwarded-Proto
            x_host=1,     # Trust X-Forwarded-Host
            x_prefix=1    # Trust X-Forwarded-Prefix
        )
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register shell context for flask shell
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
