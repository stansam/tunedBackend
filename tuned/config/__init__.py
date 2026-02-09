"""
Environment-aware configuration classes for Flask application.

Usage:
    from tuned.config import config
    app.config.from_object(config['development'])
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class BaseConfig:
    """Base configuration with common settings for all environments."""
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32).hex()
    
    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_ECHO = False
    
    # Performance
    JSON_SORT_KEYS = False
    
    # Session configuration
    SESSION_COOKIE_NAME = 'tuned_session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'None'
    SESSION_COOKIE_PATH = '/'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Flask-Login
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    
    # JWT configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or os.environ.get('SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ['headers', 'cookies']
    JWT_COOKIE_SECURE = True  # Only send over HTTPS
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_COOKIE_SAMESITE = 'None'
    JWT_ACCESS_COOKIE_NAME = 'tuned_access_token'
    JWT_REFRESH_COOKIE_NAME = 'tuned_refresh_token'
    JWT_COOKIE_PATH = '/'
    
    # Mail configuration
    MAIL_SERVER = os.environ.get('EMAIL_HOST', 'smtp.hostinger.com')
    MAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'info@tunedessays.com')
    
    # File upload limits
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file size
    
    # SocketIO
    SOCKETIO_MESSAGE_QUEUE = os.environ.get('SOCKETIO_MESSAGE_QUEUE')  # Redis URL for scaling
    
    # Redis Configuration
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # Celery Configuration
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/1')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TIMEZONE = 'UTC'
    CELERY_ENABLE_UTC = True
    
    # JWT Blacklist (Redis-based)
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    
    # Frontend URL (for email links)
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')


class DevelopmentConfig(BaseConfig):
    """Development environment configuration."""
    
    DEBUG = True
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or 'sqlite:///app.db'
    SQLALCHEMY_ECHO = False  # Set to True to see SQL queries
    
    # Server configuration
    # SERVER_NAME = os.environ.get('DEV_SERVER_NAME')  # e.g., 'tunedessays.com:5000'
    
    # CORS - Allow all origins in development
    CORS_ORIGINS = [
        'http://localhost:3000',
    ]
    
    # Security - Relaxed for local development
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    JWT_COOKIE_SECURE = False
    
    # Disable ProxyFix in development
    PROXY_FIX = False


class TestingConfig(BaseConfig):
    """Testing environment configuration."""
    
    TESTING = True
    DEBUG = True
    
    # Use in-memory SQLite for fast tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    JWT_COOKIE_CSRF_PROTECT = False
    
    # Fast sessions for testing
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=5)
    
    # Disable mail sending in tests
    MAIL_SUPPRESS_SEND = True
    
    # Security - Disabled for testing
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    JWT_COOKIE_SECURE = False


class ProductionConfig(BaseConfig):
    """Production environment configuration."""
    
    DEBUG = False
    TESTING = False
    
    # PostgreSQL database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
            user=os.environ.get('DB_USER', 'tunedop'),
            password=os.environ.get('DB_PASSWORD', ''),
            host=os.environ.get('DB_HOST', 'localhost'),
            port=os.environ.get('DB_PORT', '5432'),
            dbname=os.environ.get('DB_NAME', 'tunedessays')
        )
    
    # Production server configuration
    # SERVER_NAME = os.environ.get('SERVER_NAME')  # e.g., 'tunedessays.com'
    SESSION_COOKIE_DOMAIN = os.environ.get('SESSION_COOKIE_DOMAIN')  # e.g., '.tunedessays.com'
    
    # CORS - Restrict to specific origin(s)
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'https://tunedessays.com').split(',')
    
    # Security - Enforced in production
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_DOMAIN = os.environ.get('JWT_COOKIE_DOMAIN')
    
    # SSL redirect
    SSL_REDIRECT = os.environ.get('SSL_REDIRECT', 'True').lower() == 'true'
    
    # Enable ProxyFix for reverse proxy deployments (nginx, etc.)
    PROXY_FIX = True
    
    # Logging
    SQLALCHEMY_RECORD_QUERIES = False  # Disable in production for performance


# Configuration selector
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
