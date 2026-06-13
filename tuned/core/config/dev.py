import os
from dotenv import load_dotenv
from tuned.core.config.base import BaseConfig
from typing import Optional

load_dotenv()

class DevelopmentConfig(BaseConfig):    
    DEBUG: bool = True
    TESTING: bool = False
    
    # SQLALCHEMY_DATABASE_URI: str = os.environ.get('SQLALCHEMY_DATABASE_URI') or 'sqlite:///app.db'
    SQLALCHEMY_DATABASE_URI: str = os.environ.get('DATABASE_URL') or \
        'postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}'.format(
            user=os.environ.get('DB_USER', 'tunedop'),
            password=os.environ.get('DB_PASSWORD', ''),
            host=os.environ.get('DB_HOST', 'localhost'),
            port=os.environ.get('DB_PORT', '5432'),
            dbname=os.environ.get('DB_NAME', 'tunedessays')
        )
        
    SQLALCHEMY_ECHO: bool = False 

    SESSION_COOKIE_DOMAIN: Optional[str] = os.environ.get('SESSION_COOKIE_DOMAIN')
    SESSION_COOKIE_SECURE: bool = False
    REMEMBER_COOKIE_SECURE: bool = False
    # JWT_COOKIE_SECURE: bool = True
    # JWT_COOKIE_DOMAIN: Optional[str] = os.environ.get('JWT_COOKIE_DOMAIN')
    SSL_REDIRECT: bool = os.environ.get('SSL_REDIRECT', 'True').lower() == 'true'
    
    PROXY_FIX: bool = False

