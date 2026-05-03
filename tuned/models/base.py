from tuned.extensions import db
from datetime import datetime, timezone
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

class BaseModel(db.Model):  # type: ignore[name-defined, misc]
    __abstract__ = True
    id: Mapped[str] = mapped_column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False) 
    deleted_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    deleted_by: Mapped[Optional[str]] = mapped_column(db.String(36), db.ForeignKey('users.id'), nullable=True)