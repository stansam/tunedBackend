"""
Flask extensions initialization.

All extensions are instantiated here but not initialized with the app.
Initialization happens in the application factory (tuned/__init__.py)
to avoid circular imports and support multiple app instances.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_mail import Mail


# Database and migrations
db = SQLAlchemy()
migrate = Migrate()

# Authentication
login_manager = LoginManager()  # Session-based auth for browser clients
jwt = JWTManager()              # Token-based auth for Next.js API

# Cross-origin resource sharing for Next.js frontend
cors = CORS()

# Real-time communication (WebSocket)
# Used by: Chat, Notifications
socketio = SocketIO()

# Email service
# Used for: verification emails, password resets, notifications
mail = Mail()
