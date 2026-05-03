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


from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=naming_convention)

db = SQLAlchemy(metadata=metadata)
migrate = Migrate()
login_manager = LoginManager()
jwt = JWTManager()
cors = CORS()
socketio = SocketIO()
mail = Mail()
