import os
from dotenv import load_dotenv
from typing import Optional
from tuned.core.config.base import BaseConfig

load_dotenv()

class ProductionConfig(BaseConfig):
    DEBUG: bool = False
    TESTING: bool = False
    
    # 'postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
    SQLALCHEMY_DATABASE_URI: str = os.environ.get('DATABASE_URL') or \
        'postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}'.format(
            user=os.environ.get('DB_USER', 'tunedop'),
            password=os.environ.get('DB_PASSWORD', ''),
            host=os.environ.get('DB_HOST', 'localhost'),
            port=os.environ.get('DB_PORT', '5432'),
            dbname=os.environ.get('DB_NAME', 'tunedessays')
        )


    # SERVER_NAME = os.environ.get('SERVER_NAME')  # e.g., 'tunedessays.com'
    SESSION_COOKIE_DOMAIN: Optional[str] = os.environ.get('SESSION_COOKIE_DOMAIN')
    
    CORS_ORIGINS: list[str] = os.environ.get('CORS_ORIGINS', 'https://tunedessays.com').split(',')
    # SOCKETIO_CORS_ORIGINS: list[str] = os.environ.get('SOCKETIO_CORS_ORIGINS', 'https://tunedessays.com').split(',')
    SESSION_COOKIE_SECURE: bool = True
    REMEMBER_COOKIE_SECURE: bool = True
    SESSION_COOKIE_SAMESITE: None = None
    # JWT_COOKIE_SECURE: bool = True
    # JWT_COOKIE_DOMAIN: Optional[str] = os.environ.get('JWT_COOKIE_DOMAIN')
    
    SSL_REDIRECT: bool = os.environ.get('SSL_REDIRECT', 'True').lower() == 'true'
    
    PROXY_FIX: bool = True
    
    SQLALCHEMY_RECORD_QUERIES: bool = False 
    REDIS_HOST: str = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT: int = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_PASSWORD: str = os.environ.get('REDIS_PASSWORD', '')
    REDIS_DB: int = int(os.environ.get('REDIS_DB', 0))
    CELERY_BROKER_REDIS_DB: int = int(os.environ.get('CELERY_BROKER_REDIS_DB', 1))
    CELERY_RESULT_BACKEND_REDIS_DB: int = int(os.environ.get('CELERY_RESULT_BACKEND_REDIS_DB', 2))
    SOCKETIO_REDIS_DB: int = int(os.environ.get('SOCKETIO_REDIS_DB', 3))
    
    REDIS_URL: str = os.environ.get('REDIS_URL', f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}')
    CELERY_BROKER_URL: str = os.environ.get('CELERY_BROKER_URL', f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{CELERY_BROKER_REDIS_DB}')
    CELERY_RESULT_BACKEND: str = os.environ.get('CELERY_RESULT_BACKEND', f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{CELERY_RESULT_BACKEND_REDIS_DB}')
    SOCKETIO_MESSAGE_QUEUE: str = os.environ.get('SOCKETIO_MESSAGE_QUEUE', f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{SOCKETIO_REDIS_DB}')