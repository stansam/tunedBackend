import os
from dotenv import load_dotenv
from tuned.core.config.base import BaseConfig

load_dotenv()

class DevelopmentConfig(BaseConfig):    
    DEBUG: bool = True
    TESTING: bool = False
    
    SQLALCHEMY_DATABASE_URI: str = os.environ.get('SQLALCHEMY_DATABASE_URI') or 'sqlite:///app.db'
    SQLALCHEMY_ECHO: bool = False 

    CORS_ORIGINS: list[str] = [
        'http://localhost:3000',
    ]
    
    SESSION_COOKIE_SECURE: bool = False
    REMEMBER_COOKIE_SECURE: bool = False
    JWT_COOKIE_SECURE: bool = False
    
    PROXY_FIX: bool = False

