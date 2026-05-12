import os
from dotenv import load_dotenv
from tuned.core.config.base import BaseConfig

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

    CORS_ORIGINS: list[str] = [
        'http://localhost:3000',
    ]

    SOCKETIO_CORS_ORIGINS: list[str] = [
        'http://localhost:3000',
        'http://195.35.37.113:3000',
    ]
    
    SESSION_COOKIE_SECURE: bool = False
    REMEMBER_COOKIE_SECURE: bool = False
    JWT_COOKIE_SECURE: bool = False
    
    PROXY_FIX: bool = False

