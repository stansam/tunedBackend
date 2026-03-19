from tuned.extensions import db
from datetime import datetime, timezone
import uuid

class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    updated_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    is_deleted = db.Column(db.Boolean, default=False, nullable=False) 