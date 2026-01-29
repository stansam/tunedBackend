"""
WSGI production entry point.

Use with Gunicorn:
    gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
    
For SocketIO support with Gunicorn:
    gunicorn -k eventlet -w 1 -b 0.0.0.0:8000 wsgi:app
    
or with gevent:
    gunicorn -k gevent -w 4 -b 0.0.0.0:8000 wsgi:app
"""
from tuned import create_app

# Create production app instance
app = create_app('production')