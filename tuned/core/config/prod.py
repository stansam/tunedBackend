import os
from dotenv import load_dotenv
from tuned.core.config.base import BaseConfig

load_dotenv()

class ProductionConfig(BaseConfig):
    DEBUG: bool = False
    TESTING: bool = False
    
    SQLALCHEMY_DATABASE_URI: str = os.environ.get('DATABASE_URL') or \
        'postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
            user=os.environ.get('DB_USER', 'tunedop'),
            password=os.environ.get('DB_PASSWORD', ''),
            host=os.environ.get('DB_HOST', 'localhost'),
            port=os.environ.get('DB_PORT', '5432'),
            dbname=os.environ.get('DB_NAME', 'tunedessays')
        )

    # SERVER_NAME = os.environ.get('SERVER_NAME')  # e.g., 'tunedessays.com'
    SESSION_COOKIE_DOMAIN: str = os.environ.get('SESSION_COOKIE_DOMAIN')
    
    CORS_ORIGINS: list[str] = os.environ.get('CORS_ORIGINS', 'https://tunedessays.com').split(',')
    SESSION_COOKIE_SECURE: bool = True
    REMEMBER_COOKIE_SECURE: bool = True
    JWT_COOKIE_SECURE: bool = True
    JWT_COOKIE_DOMAIN: str = os.environ.get('JWT_COOKIE_DOMAIN')
    
    SSL_REDIRECT: bool = os.environ.get('SSL_REDIRECT', 'True').lower() == 'true'
    
    PROXY_FIX: bool = True
    
    SQLALCHEMY_RECORD_QUERIES: bool = False 
