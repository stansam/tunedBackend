from datetime import timedelta
from tuned.core.config.base import BaseConfig

class TestingConfig(BaseConfig):
    TESTING: bool = True
    DEBUG: bool = True
    SQLALCHEMY_DATABASE_URI: str = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED: bool = False
    JWT_COOKIE_CSRF_PROTECT: bool = False
    PERMANENT_SESSION_LIFETIME: timedelta = timedelta(minutes=5)
    MAIL_SUPPRESS_SEND: bool = True
    SESSION_COOKIE_SECURE: bool = False
    REMEMBER_COOKIE_SECURE: bool = False
    JWT_COOKIE_SECURE: bool = False
