"""
Development server entry point.

⚠️ WARNING: Do NOT use in production!
For production, use wsgi.py with Gunicorn or uWSGI.

Usage:
    python app.py
    
or:
    export FLASK_ENV=development
    flask run
"""
from tuned import create_app
from tuned.extensions import socketio

# Create app instance
app = create_app()

if __name__ == '__main__':
    # Use socketio.run() instead of app.run() for WebSocket support
    socketio.run(
        app,
        debug=True,
        host='0.0.0.0',
        port=5000,
        use_reloader=True
    )
